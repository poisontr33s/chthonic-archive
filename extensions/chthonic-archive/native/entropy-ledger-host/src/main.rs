use std::fs;
use std::io::{self, BufRead, Write};
use std::rc::Rc;
use std::str::FromStr;

use anchor_client::{Client, Cluster, Program};
use anchor_lang::AnchorSerialize;
use anyhow::{Context, Result};
use clap::Parser;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use solana_sdk::instruction::{AccountMeta, Instruction};
use solana_sdk::pubkey::Pubkey;
use solana_sdk::signature::{read_keypair_file, Keypair, Signature};
use solana_sdk::signer::Signer;
use solana_sdk::{commitment_config::CommitmentConfig, system_program};

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

#[derive(Debug, Serialize)]
struct SubmitEntropyResult {
    signature: String,
    slot: u64,
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

#[derive(Debug, AnchorSerialize)]
struct RecordDecayArgs {
    entropy_score: u64,
    merkle_root: [u8; 32],
}

fn main() -> Result<()> {
    let opts = Opts::parse();
    let wallet = read_keypair_file(&opts.wallet).context("wallet not found or unreadable")?;
    let authority = wallet.pubkey();
    let payer = Rc::new(wallet);

    let program_id = resolve_program_id(&opts)?;
    let cluster = Cluster::Custom(opts.rpc_url.clone(), opts.rpc_url.clone());
    let client = Client::new_with_options(cluster, payer, CommitmentConfig::confirmed());
    let program = client
        .program(program_id)
        .context("failed to initialize anchor client program handle")?;

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

        match submit_entropy(&program, authority, params.entropy_score, &params.merkle_root) {
            Ok((signature, slot)) => {
                write_json(&JsonRpcSuccess {
                    jsonrpc: "2.0",
                    id: request.id,
                    result: SubmitEntropyResult {
                        signature: signature.to_string(),
                        slot,
                    },
                })?;
            }
            Err(error) => {
                write_json(&JsonRpcError {
                    jsonrpc: "2.0",
                    id: request.id,
                    error: ErrorPayload {
                        code: -32000,
                        message: error.to_string(),
                    },
                })?;
            }
        }
    }

    Ok(())
}

fn submit_entropy(
    program: &Program<Rc<Keypair>>,
    authority: Pubkey,
    entropy_score: u64,
    merkle_root_hex: &str,
) -> Result<(Signature, u64)> {
    let merkle_root = decode_merkle_root(merkle_root_hex)?;
    let program_id = program.id();
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

    let signature = program
        .request()
        .instruction(instruction)
        .send()
        .context("failed to submit anchor record_decay transaction")?;

    let slot = program
        .rpc()
        .get_slot()
        .context("failed to read latest slot after submission")?;

    Ok((signature, slot))
}

fn build_record_decay_instruction_data(entropy_score: u64, merkle_root: [u8; 32]) -> Result<Vec<u8>> {
    let args = RecordDecayArgs {
        entropy_score,
        merkle_root,
    };
    let mut data = instruction_discriminator("record_decay").to_vec();
    data.extend(args.try_to_vec().context("failed to serialize record_decay args")?);
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
