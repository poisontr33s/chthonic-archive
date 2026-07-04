// Static hardware inventory via native WMI — no PowerShell subprocess.
//
// wmi::WMIConnection::new() initializes COM internally; async_query() is the
// crate's own async-safe query path (used as documented — no manual COM
// apartment handling layered on top of what the crate already provides).
//
// WMI's uint64 CIM properties (Capacity, Size) are a known wire-format
// ambiguity: some paths surface them as Variant::String, others as a native
// integer variant, depending on provider and OS build. de_u64_flex accepts
// either shape rather than betting on one — this is an external-API boundary
// with real, undocumented variance, not speculative defensiveness.

#![allow(non_snake_case)]

use serde::{Deserialize, Serialize};
use wmi::WMIConnection;

fn de_u64_flex<'de, D>(deserializer: D) -> Result<u64, D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct FlexVisitor;
    impl<'de> serde::de::Visitor<'de> for FlexVisitor {
        type Value = u64;
        fn expecting(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
            write!(f, "a u64 or a string containing one")
        }
        fn visit_u64<E>(self, v: u64) -> Result<u64, E> {
            Ok(v)
        }
        fn visit_i64<E>(self, v: i64) -> Result<u64, E> {
            Ok(v.max(0) as u64)
        }
        fn visit_str<E>(self, v: &str) -> Result<u64, E>
        where
            E: serde::de::Error,
        {
            v.parse().map_err(serde::de::Error::custom)
        }
    }
    deserializer.deserialize_any(FlexVisitor)
}

fn de_opt_u64_flex<'de, D>(deserializer: D) -> Result<Option<u64>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct OptFlexVisitor;
    impl<'de> serde::de::Visitor<'de> for OptFlexVisitor {
        type Value = Option<u64>;
        fn expecting(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
            write!(f, "an optional u64 or string containing one")
        }
        fn visit_none<E>(self) -> Result<Option<u64>, E> {
            Ok(None)
        }
        fn visit_unit<E>(self) -> Result<Option<u64>, E> {
            Ok(None)
        }
        fn visit_some<D2>(self, deserializer: D2) -> Result<Option<u64>, D2::Error>
        where
            D2: serde::Deserializer<'de>,
        {
            de_u64_flex(deserializer).map(Some)
        }
    }
    deserializer.deserialize_option(OptFlexVisitor)
}

#[derive(Deserialize, Debug, Clone)]
struct Win32_Processor {
    Name: String,
    Manufacturer: String,
    NumberOfCores: u32,
    NumberOfLogicalProcessors: u32,
    MaxClockSpeed: u32,
}

#[derive(Deserialize, Debug, Clone)]
struct Win32_PhysicalMemory {
    Manufacturer: Option<String>,
    PartNumber: Option<String>,
    #[serde(deserialize_with = "de_u64_flex")]
    Capacity: u64,
    Speed: Option<u32>,
    ConfiguredClockSpeed: Option<u32>,
    BankLabel: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
struct Win32_DiskDrive {
    Model: Option<String>,
    #[serde(default, deserialize_with = "de_opt_u64_flex")]
    Size: Option<u64>,
    InterfaceType: Option<String>,
    MediaType: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
struct Win32_BaseBoard {
    Manufacturer: Option<String>,
    Product: Option<String>,
    SerialNumber: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
struct Win32_BIOS {
    SMBIOSBIOSVersion: Option<String>,
    ReleaseDate: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CpuInfo {
    pub name: String,
    pub manufacturer: String,
    pub physical_cores: u32,
    pub logical_processors: u32,
    pub max_clock_mhz: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MemoryModule {
    pub manufacturer: Option<String>,
    pub part_number: Option<String>,
    pub capacity_bytes: u64,
    /// SMBIOS-rated speed (MHz). WMI's schema documents this field's unit as
    /// "nanoseconds" (a stale CIM_PhysicalMemory base-class holdover) but the
    /// SMBIOS-sourced runtime value is MT/s, universally read as MHz by every
    /// consumer (Task Manager, HWiNFO, etc.) — reported as-is here.
    pub speed_mhz: Option<u32>,
    /// Actual running clock (differs from speed_mhz under XMP/EXPO profiles).
    pub configured_clock_mhz: Option<u32>,
    pub bank_label: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DiskInfo {
    pub model: Option<String>,
    pub size_bytes: Option<u64>,
    pub interface_type: Option<String>,
    pub media_type: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct BoardInfo {
    pub manufacturer: Option<String>,
    pub product: Option<String>,
    pub serial_number: Option<String>,
    pub bios_version: Option<String>,
    pub bios_release_date: Option<String>,
}

type Inventory = (
    Option<CpuInfo>,
    Vec<MemoryModule>,
    Vec<DiskInfo>,
    Option<BoardInfo>,
);

/// WMIConnection wraps raw COM pointers (IWbemServices/IUnknown) and is
/// !Send — it cannot cross an .await point inside a future that rmcp's
/// #[tool] macro needs to box as Send. Running the whole synchronous query
/// sequence inside spawn_blocking keeps the !Send connection confined to one
/// blocking-pool thread; only the owned, Send-safe result tuple crosses back.
pub async fn collect_all() -> Inventory {
    tokio::task::spawn_blocking(collect_all_blocking)
        .await
        .unwrap_or_else(|e| {
            tracing::warn!("WMI collection task panicked: {e}");
            (None, Vec::new(), Vec::new(), None)
        })
}

fn collect_all_blocking() -> Inventory {
    let wmi_con = match WMIConnection::new() {
        Ok(c) => c,
        Err(e) => {
            tracing::warn!("WMI connection failed: {e}");
            return (None, Vec::new(), Vec::new(), None);
        }
    };

    let cpu = match wmi_con.query::<Win32_Processor>() {
        Ok(v) => v.into_iter().next().map(|p| CpuInfo {
            name: p.Name,
            manufacturer: p.Manufacturer,
            physical_cores: p.NumberOfCores,
            logical_processors: p.NumberOfLogicalProcessors,
            max_clock_mhz: p.MaxClockSpeed,
        }),
        Err(e) => {
            tracing::warn!("Win32_Processor query failed: {e}");
            None
        }
    };

    let memory = match wmi_con.query::<Win32_PhysicalMemory>() {
        Ok(v) => v
            .into_iter()
            .map(|m| MemoryModule {
                manufacturer: m.Manufacturer,
                part_number: m.PartNumber,
                capacity_bytes: m.Capacity,
                speed_mhz: m.Speed,
                configured_clock_mhz: m.ConfiguredClockSpeed,
                bank_label: m.BankLabel,
            })
            .collect(),
        Err(e) => {
            tracing::warn!("Win32_PhysicalMemory query failed: {e}");
            Vec::new()
        }
    };

    let storage = match wmi_con.query::<Win32_DiskDrive>() {
        Ok(v) => v
            .into_iter()
            .map(|d| DiskInfo {
                model: d.Model,
                size_bytes: d.Size,
                interface_type: d.InterfaceType,
                media_type: d.MediaType,
            })
            .collect(),
        Err(e) => {
            tracing::warn!("Win32_DiskDrive query failed: {e}");
            Vec::new()
        }
    };

    let bios = wmi_con
        .query::<Win32_BIOS>()
        .ok()
        .and_then(|v| v.into_iter().next());

    let board = match wmi_con.query::<Win32_BaseBoard>() {
        Ok(v) => v.into_iter().next().map(|b| BoardInfo {
            manufacturer: b.Manufacturer,
            product: b.Product,
            serial_number: b.SerialNumber,
            bios_version: bios.as_ref().and_then(|x| x.SMBIOSBIOSVersion.clone()),
            bios_release_date: bios.as_ref().and_then(|x| x.ReleaseDate.clone()),
        }),
        Err(e) => {
            tracing::warn!("Win32_BaseBoard query failed: {e}");
            None
        }
    };

    (cpu, memory, storage, board)
}
