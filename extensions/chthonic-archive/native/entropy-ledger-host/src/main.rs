use std::fs;
use std::io::{self, BufRead, Write};
use std::str::FromStr;

use anyhow::{anyhow, Context, Result};
use base64::prelude::{Engine as _, BASE64_STANDARD};
use borsh::BorshSerialize;
use clap::Parser;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use solana_hash::Hash;
use solana_instruction::{AccountMeta, Instruction};
use solana_keypair::{read_keypair_file, Keypair};
use solana_pubkey::Pubkey;
use solana_signer::Signer;
use solana_system_interface::program as system_program;
use solana_transaction::Transaction;

#[derive(Parser, Debug)]
#[command(name = "entropy-ledger-host")]
struct Opts {
    #[arg(long, default_value = ".chthonic/wallets/payer.json")]
    wallet: String,
    #[arg(long, default_value = ".chthonic/wallets/entropy_ledger.json")]
    idl: String,
    #[arg(long, default_value = "http://127.0.0.1:8899")]
    rpc_url: String,
    #[arg(long)]
    program_id: Option<String>,
    /// Offline dry-run: build + sign + serialize + self-verify and emit exactly
    /// what WOULD be broadcast — but never contact the network. A missing wallet
    /// becomes a throwaway keypair; the blockhash is a dummy so the result can
    /// never be sent by accident. Safe sandbox for prototyping before live.
    #[arg(long)]
    offline: bool,
}

#[derive(Debug, Deserialize)]
struct JsonRpcRequest {
    id: u64,
    method: String,
    params: Option<SubmitEntropyParams>,
}

#[derive(Debug, Deserialize)]
struct SubmitEntropyParams {
    entropy_score: u64,
    merkle_root: String,
    #[allow(dead_code)]
    leaf_count: Option<u64>,
    #[allow(dead_code)]
    reason: Option<String>,
}

#[derive(Debug, Serialize)]
struct JsonRpcSuccess<'a, T> {
    jsonrpc: &'a str,
    id: u64,
    result: T,
}

#[derive(Debug, Serialize)]
struct JsonRpcError<'a> {
    jsonrpc: &'a str,
    id: u64,
    error: ErrorPayload,
}

#[derive(Debug, Serialize)]
struct ErrorPayload {
    code: i32,
    message: String,
}

/// Live-mode result: the chain accepted the transaction.
#[derive(Debug, Serialize)]
struct SubmitEntropyResult {
    signature: String,
    slot: u64,
}

/// Offline-mode result: the fully-built, signed, self-verified transaction that
/// WOULD be broadcast — emitted for inspection, never sent.
#[derive(Debug, Serialize)]
struct OfflineDryRunResult {
    mode: &'static str,
    note: &'static str,
    program_id: String,
    signer: String,
    ledger_pda: String,
    discriminator_hex: String,
    entropy_score: u64,
    merkle_root: String,
    accounts: Vec<DecodedAccount>,
    signature: String,
    blockhash: String,
    wire_bytes: usize,
    wire_base64: String,
    self_verified: bool,
}

#[derive(Debug, Serialize)]
struct DecodedAccount {
    pubkey: String,
    is_signer: bool,
    is_writable: bool,
    role: &'static str,
}

#[derive(Debug, Deserialize)]
struct AnchorIdl {
    #[serde(default)]
    address: Option<String>,
    #[serde(default)]
    metadata: Option<AnchorIdlMetadata>,
}

#[derive(Debug, Deserialize)]
struct AnchorIdlMetadata {
    #[serde(default)]
    address: Option<String>,
}

#[derive(Debug, BorshSerialize)]
struct RecordDecayArgs {
    entropy_score: u64,
    merkle_root: [u8; 32],
}

// ---------------------------------------------------------------------------
// Online layer: a thin JSON-RPC-over-HTTP client. Online, Solana is a stable,
// versionless wire protocol — far less brittle than the solana-rpc-client crate
// it replaces. Only `submit_live` touches this; the offline path never does.
// ---------------------------------------------------------------------------

struct RpcHttp {
    url: String,
    client: reqwest::blocking::Client,
    commitment: String,
}

impl RpcHttp {
    fn new(url: String) -> Self {
        Self {
            url,
            client: reqwest::blocking::Client::new(),
            commitment: "confirmed".to_string(),
        }
    }

    fn call(&self, method: &str, params: Value) -> Result<Value> {
        let body = json!({ "jsonrpc": "2.0", "id": 1, "method": method, "params": params });
        let response: Value = self
            .client
            .post(&self.url)
            .json(&body)
            .send()
            .with_context(|| format!("HTTP POST to {} for {method} failed", self.url))?
            .json()
            .with_context(|| format!("decoding {method} response as JSON failed"))?;
        if let Some(error) = response.get("error") {
            if !error.is_null() {
                anyhow::bail!("RPC {method} error: {error}");
            }
        }
        response
            .get("result")
            .cloned()
            .ok_or_else(|| anyhow!("RPC {method}: response carried no result"))
    }

    fn get_latest_blockhash(&self) -> Result<Hash> {
        let result = self.call("getLatestBlockhash", json!([{ "commitment": self.commitment }]))?;
        let blockhash = result["value"]["blockhash"]
            .as_str()
            .ok_or_else(|| anyhow!("getLatestBlockhash: no blockhash in response"))?;
        Hash::from_str(blockhash)
            .map_err(|error| anyhow!("getLatestBlockhash: invalid base58 blockhash: {error}"))
    }

    fn send_transaction(&self, wire_base64: &str) -> Result<String> {
        let result = self.call(
            "sendTransaction",
            json!([wire_base64, { "encoding": "base64", "preflightCommitment": self.commitment }]),
        )?;
        result
            .as_str()
            .map(str::to_string)
            .ok_or_else(|| anyhow!("sendTransaction: no signature in result"))
    }

    /// Poll until the signature reaches the configured commitment (replaces what
    /// solana-rpc-client's send_and_confirm did for us). Bounded so a stuck tx
    /// surfaces as an error rather than hanging forever.
    fn confirm(&self, signature: &str) -> Result<()> {
        for _ in 0..60 {
            let result = self.call(
                "getSignatureStatuses",
                json!([[signature], { "searchTransactionHistory": false }]),
            )?;
            if let Some(status) = result["value"].get(0) {
                if !status.is_null() {
                    if let Some(err) = status.get("err") {
                        if !err.is_null() {
                            anyhow::bail!("transaction failed on-chain: {err}");
                        }
                    }
                    if let Some(level) = status["confirmationStatus"].as_str() {
                        if level == "confirmed" || level == "finalized" {
                            return Ok(());
                        }
                    }
                }
            }
            std::thread::sleep(std::time::Duration::from_millis(500));
        }
        anyhow::bail!("transaction not confirmed within timeout")
    }

    fn get_slot(&self) -> Result<u64> {
        let result = self.call("getSlot", json!([{ "commitment": self.commitment }]))?;
        result
            .as_u64()
            .ok_or_else(|| anyhow!("getSlot: non-numeric slot in response"))
    }
}

fn main() -> Result<()> {
    let opts = Opts::parse();

    let wallet = load_wallet(&opts)?;
    let program_id = resolve_program_id_or_placeholder(&opts)?;
    let rpc = if opts.offline {
        None
    } else {
        Some(RpcHttp::new(opts.rpc_url.clone()))
    };

    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        let raw = line?;
        let trimmed = raw.trim();
        if trimmed.is_empty() {
            continue;
        }
        let request = match serde_json::from_str::<JsonRpcRequest>(trimmed) {
            Ok(value) => value,
            Err(error) => {
                write_json(&JsonRpcError {
                    jsonrpc: "2.0",
                    id: 0,
                    error: ErrorPayload {
                        code: -32700,
                        message: format!("invalid JSON: {error}"),
                    },
                })?;
                continue;
            }
        };

        if request.method != "submit_entropy" {
            write_json(&JsonRpcError {
                jsonrpc: "2.0",
                id: request.id,
                error: ErrorPayload {
                    code: -32601,
                    message: format!("unknown method {}", request.method),
                },
            })?;
            continue;
        }

        let params = match request.params {
            Some(value) => value,
            None => {
                write_json(&JsonRpcError {
                    jsonrpc: "2.0",
                    id: request.id,
                    error: ErrorPayload {
                        code: -32602,
                        message: "missing params".to_string(),
                    },
                })?;
                continue;
            }
        };

        if opts.offline {
            match dry_run_offline(&wallet, program_id, params.entropy_score, &params.merkle_root) {
                Ok(result) => write_json(&JsonRpcSuccess {
                    jsonrpc: "2.0",
                    id: request.id,
                    result,
                })?,
                Err(error) => write_json(&JsonRpcError {
                    jsonrpc: "2.0",
                    id: request.id,
                    error: ErrorPayload {
                        code: -32000,
                        message: error.to_string(),
                    },
                })?,
            }
        } else {
            let rpc = rpc.as_ref().expect("live mode constructs an RpcHttp");
            match submit_live(rpc, &wallet, program_id, params.entropy_score, &params.merkle_root) {
                Ok(result) => write_json(&JsonRpcSuccess {
                    jsonrpc: "2.0",
                    id: request.id,
                    result,
                })?,
                Err(error) => write_json(&JsonRpcError {
                    jsonrpc: "2.0",
                    id: request.id,
                    error: ErrorPayload {
                        code: -32000,
                        message: error.to_string(),
                    },
                })?,
            }
        }
    }

    Ok(())
}

/// Live path: fetch a real blockhash, sign, serialize, broadcast, confirm.
fn submit_live(
    rpc: &RpcHttp,
    payer: &Keypair,
    program_id: Pubkey,
    entropy_score: u64,
    merkle_root_hex: &str,
) -> Result<SubmitEntropyResult> {
    let merkle_root = decode_merkle_root(merkle_root_hex)?;
    let authority = payer.pubkey();
    let (instruction, _ledger_pda) =
        build_record_decay_ix(authority, program_id, entropy_score, merkle_root)?;

    let recent_blockhash = rpc.get_latest_blockhash()?;
    let transaction =
        Transaction::new_signed_with_payer(&[instruction], Some(&authority), &[payer], recent_blockhash);
    let wire_base64 = serialize_transaction_base64(&transaction)?;

    let signature = rpc.send_transaction(&wire_base64)?;
    rpc.confirm(&signature)?;
    let slot = rpc.get_slot()?;

    Ok(SubmitEntropyResult { signature, slot })
}

/// Offline path: identical construction/signing/serialization, a DUMMY blockhash,
/// and two self-checks (signature validity + wire round-trip). Emits the artifact
/// for inspection; never broadcasts. Byte-identical to live except the blockhash.
fn dry_run_offline(
    payer: &Keypair,
    program_id: Pubkey,
    entropy_score: u64,
    merkle_root_hex: &str,
) -> Result<OfflineDryRunResult> {
    let merkle_root = decode_merkle_root(merkle_root_hex)?;
    let authority = payer.pubkey();
    let (instruction, ledger_pda) =
        build_record_decay_ix(authority, program_id, entropy_score, merkle_root)?;

    let accounts: Vec<DecodedAccount> = instruction
        .accounts
        .iter()
        .enumerate()
        .map(|(index, meta)| DecodedAccount {
            pubkey: meta.pubkey.to_string(),
            is_signer: meta.is_signer,
            is_writable: meta.is_writable,
            role: match index {
                0 => "ledger_state (PDA, writable)",
                1 => "authority (payer / signer)",
                2 => "system_program",
                _ => "extra",
            },
        })
        .collect();

    // Dummy all-zero blockhash: a structurally real, fully signed transaction that
    // is deliberately NOT a valid recent blockhash — so it can never be broadcast
    // by accident, even if the base64 leaks into a live sender.
    let blockhash = Hash::new_from_array([0u8; 32]);
    let blockhash_str = blockhash.to_string();
    let transaction =
        Transaction::new_signed_with_payer(&[instruction], Some(&authority), &[payer], blockhash);

    // Self-check 1: the signature is cryptographically valid over the message we
    // built — pure offline ed25519, no network.
    transaction
        .verify()
        .map_err(|error| anyhow!("offline signature verification failed: {error}"))?;

    // Self-check 2: the wire bytes round-trip losslessly (deserialize → re-serialize
    // → identical). This is the exact encoding sendTransaction would receive.
    let wire = bincode::serialize(&transaction).context("wire serialization failed")?;
    let decoded: Transaction =
        bincode::deserialize(&wire).context("wire round-trip deserialize failed")?;
    let reserialized = bincode::serialize(&decoded).context("wire re-serialization failed")?;
    anyhow::ensure!(
        wire == reserialized,
        "wire round-trip mismatch — serialization is not stable"
    );

    Ok(OfflineDryRunResult {
        mode: "offline-dry-run",
        note: "Built, signed, serialized and self-verified OFFLINE. Dummy zero blockhash → NOT broadcastable. No network contacted, no funds at risk.",
        program_id: program_id.to_string(),
        signer: authority.to_string(),
        ledger_pda: ledger_pda.to_string(),
        discriminator_hex: hex::encode(instruction_discriminator("record_decay")),
        entropy_score,
        merkle_root: merkle_root_hex.to_string(),
        accounts,
        signature: transaction.signatures[0].to_string(),
        blockhash: blockhash_str,
        wire_bytes: wire.len(),
        wire_base64: BASE64_STANDARD.encode(&wire),
        self_verified: true,
    })
}

/// The instruction is built identically for both modes — same discriminator,
/// args, accounts, and PDA. This is the deterministic offline core.
fn build_record_decay_ix(
    authority: Pubkey,
    program_id: Pubkey,
    entropy_score: u64,
    merkle_root: [u8; 32],
) -> Result<(Instruction, Pubkey)> {
    let ledger_state = derive_ledger_address(authority, program_id);
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(ledger_state, false),
            AccountMeta::new_readonly(authority, true),
            AccountMeta::new_readonly(system_program::ID, false),
        ],
        data: build_record_decay_instruction_data(entropy_score, merkle_root)?,
    };
    Ok((instruction, ledger_state))
}

/// Canonical Solana wire encoding: bincode (short-vec via the serde feature) +
/// base64. Mirrors exactly what solana-rpc-client did internally.
fn serialize_transaction_base64(transaction: &Transaction) -> Result<String> {
    let wire = bincode::serialize(transaction).context("failed to serialize transaction")?;
    Ok(BASE64_STANDARD.encode(wire))
}

fn build_record_decay_instruction_data(entropy_score: u64, merkle_root: [u8; 32]) -> Result<Vec<u8>> {
    let args = RecordDecayArgs {
        entropy_score,
        merkle_root,
    };
    let mut data = instruction_discriminator("record_decay").to_vec();
    data.extend(borsh::to_vec(&args).context("failed to serialize record_decay args")?);
    Ok(data)
}

fn instruction_discriminator(name: &str) -> [u8; 8] {
    let mut hasher = Sha256::new();
    hasher.update(format!("global:{name}").as_bytes());
    let digest = hasher.finalize();
    let mut discriminator = [0_u8; 8];
    discriminator.copy_from_slice(&digest[..8]);
    discriminator
}

fn decode_merkle_root(input: &str) -> Result<[u8; 32]> {
    let bytes = hex::decode(input).context("merkle_root must be hex-encoded")?;
    if bytes.len() != 32 {
        anyhow::bail!("merkle_root must decode to 32 bytes");
    }
    let mut out = [0_u8; 32];
    out.copy_from_slice(&bytes);
    Ok(out)
}

fn derive_ledger_address(authority: Pubkey, program_id: Pubkey) -> Pubkey {
    let (pda, _bump) = Pubkey::find_program_address(&[b"ledger", authority.as_ref()], &program_id);
    pda
}

/// Load the payer wallet. Offline mode tolerates a missing file by minting a
/// throwaway keypair (no funds, never broadcast) so mechanics can be exercised
/// with nothing at stake. Live mode requires a real wallet.
fn load_wallet(opts: &Opts) -> Result<Keypair> {
    match read_keypair_file(&opts.wallet) {
        Ok(keypair) => Ok(keypair),
        Err(error) if opts.offline => {
            eprintln!(
                "[offline] wallet '{}' not found ({error}); minting a throwaway keypair — no funds, never broadcast.",
                opts.wallet
            );
            Ok(Keypair::new())
        }
        Err(error) => Err(anyhow!("wallet not found or unreadable: {error}")),
    }
}

/// Resolve the program id. Offline mode tolerates an unresolvable id with an
/// obvious placeholder (the system program) so a dry-run needs no IDL on disk;
/// pass --program-id for a faithful decode. Live mode requires a real id.
fn resolve_program_id_or_placeholder(opts: &Opts) -> Result<Pubkey> {
    match resolve_program_id(opts) {
        Ok(program_id) => Ok(program_id),
        Err(error) if opts.offline => {
            eprintln!(
                "[offline] program id unresolved ({error}); using placeholder 11111111111111111111111111111111 — pass --program-id for a real decode."
            );
            Pubkey::from_str("11111111111111111111111111111111")
                .context("placeholder program id is invalid (unreachable)")
        }
        Err(error) => Err(error),
    }
}

fn resolve_program_id(opts: &Opts) -> Result<Pubkey> {
    if let Some(raw) = &opts.program_id {
        return Pubkey::from_str(raw).context("invalid --program-id");
    }

    let idl_raw = fs::read_to_string(&opts.idl).context("unable to read anchor IDL")?;
    let idl: AnchorIdl = serde_json::from_str(&idl_raw).context("failed to parse anchor IDL JSON")?;
    let from_idl = idl
        .metadata
        .and_then(|metadata| metadata.address)
        .or(idl.address);

    match from_idl {
        Some(value) => Pubkey::from_str(&value).context("invalid program ID in IDL"),
        None => anyhow::bail!("unable to resolve program ID; pass --program-id or include metadata.address in IDL"),
    }
}

fn write_json<T: Serialize>(value: &T) -> Result<()> {
    let encoded = serde_json::to_string(value)?;
    let mut stdout = io::stdout().lock();
    stdout.write_all(encoded.as_bytes())?;
    stdout.write_all(b"\n")?;
    stdout.flush()?;
    Ok(())
}
