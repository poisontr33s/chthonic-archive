# PROSJEKT: BridgeTroll - Systematisk Konfigurasjons- og Versjonsrevisjon

## KONTEKST OG ROLLE
Du opererer nå som eksekverende agent for prosjekt "BridgeTroll" i et lokalt Windows 11-miljø. Din oppgave er å traversere, analysere og validere konfigurasjons- og versjonstilstanden for et spesifikt "native-first" poly-repo, og deretter generere to handlingsorienterte rapporter.

**Målkatalog:** `C:\Users\eldno\chthonic-archive`
*(Viktig: Du skal KUN analysere hovedarkivet. Du må eksplisitt ignorere alle symlinks/junksjoner til nedlastede søster-repositorier for å unngå blanding av kontekst).*

## FASE 1: OPPDAGELSE OG TRAVERSERING
Søk gjennom målkatalogen og trekk ut innholdet fra følgende filtyper og konfigurasjoner:
1. Alle `.toml` filer (spesielt `mise.toml`, `.cargo/config.toml`).
2. Alle `.json` konfigurasjonsfiler knyttet til verktøykjedene nevnt under.
3. Lock-filer for pakke- og versjonshåndterere.

## FASE 2: VERKTØY- OG VERSJONSANALYSE (TILSTAND A MOT B)
For hver av de følgende domenesiloene, les de lokale innstillingene (Versjon A / Tilstand A) og gjør et oppslag mot offisielle registre/kilder for å finne siste stabile versjon og best practice (Versjon B / Tilstand B):

* **Python (Astral-stack):** Sjekk innstillinger, lock-filer og miljøvariabler for `uv`, `uv tool`, `uv pip`, og `uv python`.
* **Ruby:** Sjekk `rv` `rv tool`, `rv ruby`  (Spinel).
* **R:** Sjekk `rv-r` (A2-ai) - *Merk: Dette er omdøpt fra rv for å unngå kollisjon med PowerShells Remove-Variable og Spinel rv.*
* **Zig:** Sjekk `zv` (Weezy20) / ZLS-innstillinger.
* **Go & C-familien (C, C#, C++):** Sjekk `goup` og prosjektkonfigurasjoner.
* **Rust:** Sjekk `.cargo/config.toml`, toolchain-filer og pakkelåser.
* **Git:** Sjekk Windows-spesifikk git-konfigurasjon (inkludert msys/bash-avhengigheter).
* **Grafikk/System:** Sjekk registry, Windows 11 miljøvariabler, og lokale paths for Nvidia-drivernivå og Vulkan SDK.

## FASE 3: GENERERING AV ARTEFAKTER
Basert på funnene i Fase 1 og 2, generer to filer i roten av `C:\Users\eldno\chthonic-archive`:

### 1. Opprett: `ROAST.md`
En direkte, analytisk og kompromissløs gjennomgang av nåværende tilstand. Må inneholde:
- Identifisering av utdaterte versjoner (A vs B) for alle nevnte språk-managers og verktøy.
- Kritikk av inkompatible, uhensiktsmessige eller utdaterte flagg/innstillinger i `.toml` og `.json` filene.
- Detektering av manglende eller feilkonfigurerte miljøvariabler for Vulkan/Nvidia i Win11.

### 2. Opprett: `TODO.md`
En strengt formatert, handlingsorientert instruksjonsliste. Må inneholde:
- Eksakte CLI-kommandoer (Windows/PowerShell) for å oppdatere samtlige identifiserte utdaterte verktøy (f.eks. oppdateringskommandoer for `uv`, `zv`, `rv`, `rv-r`).
- Spesifikke filstier og linjenummer med nøyaktig syntaks for hva som må overskrives i `.toml`/`.json`-filene.
- Kodelinjer for å oppdatere nødvendige Windows 11 miljøvariabler (`$env:PATH` etc.).

Start umiddelbart med traversering av filsystemet og gi meg deretter en bekreftelse på at `ROAST.md` og `TODO.md` er generert.