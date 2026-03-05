---
sid: FORGE_VSCONFIG_DECISION_RECORD_V1
title: Recovered VS Toolchain Decision Record
created: 2026-03-05T16:18:24+00:00
source_files: ["codex/mailbox/SSMS22_ACTUAL_INSTALLED_20260218.vsconfig", "codex/mailbox/VS2026_BUILDTOOLS_EXPORT.vsconfig", "codex/mailbox/VS2026_COMMUNITY_EXPORT.vsconfig", "codex/mailbox/VS_BUILDTOOLS_INSIDERS_ACTUAL_INSTALLED_20260218.vsconfig", "codex/mailbox/VS_PRO_INSIDERS_ACTUAL_INSTALLED_20260218.vsconfig"]
pathway: vsconfig -> component diff -> decision record
kept: Shared and divergent Visual Studio workload selections.
discarded: Redundant snapshot serialization once the comparison exists.
---
# VS Toolchain Decision Record

- Snapshots compared: 5
- Common components: 0
- Union components: 229

## Shared Components


## Snapshot Deltas

### codex/mailbox/SSMS22_ACTUAL_INSTALLED_20260218.vsconfig

- `Microsoft.SSMS.Component.Core`
- `Microsoft.VisualStudio.Component.CoreEditor`
- `Microsoft.VisualStudio.Product.Ssms`
- `Microsoft.VisualStudio.Workload.SSMSCore`

### codex/mailbox/VS2026_BUILDTOOLS_EXPORT.vsconfig

- `Microsoft.Component.MSBuild`
- `Microsoft.VisualStudio.Component.CoreBuildTools`
- `Microsoft.VisualStudio.Component.Roslyn.Compiler`
- `Microsoft.VisualStudio.Component.TestTools.BuildTools`
- `Microsoft.VisualStudio.Component.TextTemplating`
- `Microsoft.VisualStudio.Component.VC.ASAN`
- `Microsoft.VisualStudio.Component.VC.CMake.Project`
- `Microsoft.VisualStudio.Component.VC.CoreBuildTools`
- `Microsoft.VisualStudio.Component.VC.Llvm.Clang`
- `Microsoft.VisualStudio.Component.VC.Llvm.ClangToolset`
- `Microsoft.VisualStudio.Component.VC.Redist.14.Latest`
- `Microsoft.VisualStudio.Component.VC.Tools.x86.x64`
- `Microsoft.VisualStudio.Component.Vcpkg`
- `Microsoft.VisualStudio.Component.Windows10SDK`
- `Microsoft.VisualStudio.Component.Windows11SDK.26100`
- `Microsoft.VisualStudio.ComponentGroup.NativeDesktop.Core`
- `Microsoft.VisualStudio.Workload.MSBuildTools`
- `Microsoft.VisualStudio.Workload.VCTools`

### codex/mailbox/VS2026_COMMUNITY_EXPORT.vsconfig

- `Component.Linux.CMake`
- `Component.MDD.Linux`
- `Component.Microsoft.NET.AppModernization`
- `Component.VisualStudio.GitHub.Copilot`
- `ComponentGroup.Microsoft.NET.AppModernization`
- `Microsoft.Component.MSBuild`
- `Microsoft.VisualStudio.Component.CoreEditor`
- `Microsoft.VisualStudio.Component.CppBuildInsights`
- `Microsoft.VisualStudio.Component.Debugger.JustInTime`
- `Microsoft.VisualStudio.Component.DiagnosticTools`
- `Microsoft.VisualStudio.Component.Graphics.Tools`
- `Microsoft.VisualStudio.Component.HLSL`
- `Microsoft.VisualStudio.Component.IntelliCode`
- `Microsoft.VisualStudio.Component.NuGet`
- `Microsoft.VisualStudio.Component.Roslyn.Compiler`
- `Microsoft.VisualStudio.Component.Roslyn.LanguageServices`
- `Microsoft.VisualStudio.Component.TextTemplating`
- `Microsoft.VisualStudio.Component.VC.ASAN`
- `Microsoft.VisualStudio.Component.VC.ATL`
- `Microsoft.VisualStudio.Component.VC.CMake.Project`
- `Microsoft.VisualStudio.Component.VC.CoreIde`
- `Microsoft.VisualStudio.Component.VC.DiagnosticTools`
- `Microsoft.VisualStudio.Component.VC.Llvm.Clang`
- `Microsoft.VisualStudio.Component.VC.Llvm.ClangToolset`
- `Microsoft.VisualStudio.Component.VC.Redist.14.Latest`
- `Microsoft.VisualStudio.Component.VC.TestAdapterForBoostTest`
- `Microsoft.VisualStudio.Component.VC.TestAdapterForGoogleTest`
- `Microsoft.VisualStudio.Component.VC.Tools.x86.x64`
- `Microsoft.VisualStudio.Component.Vcpkg`
- `Microsoft.VisualStudio.Component.Windows10SDK`
- `Microsoft.VisualStudio.Component.Windows11SDK.26100`
- `Microsoft.VisualStudio.Component.Windows11Sdk.WindowsPerformanceToolkit`
- `Microsoft.VisualStudio.ComponentGroup.NativeDesktop.Core`
- `Microsoft.VisualStudio.ComponentGroup.WebToolsExtensions`
- `Microsoft.VisualStudio.ComponentGroup.WebToolsExtensions.CMake`
- `Microsoft.VisualStudio.Workload.CoreEditor`
- `Microsoft.VisualStudio.Workload.NativeDesktop`
- `Microsoft.VisualStudio.Workload.NativeGame`

### codex/mailbox/VS_BUILDTOOLS_INSIDERS_ACTUAL_INSTALLED_20260218.vsconfig

- `Component.Android.SDK.MAUI`
- `Component.LinuxBuildTools`
- `Component.Microsoft.Windows.DriverKit.BuildTools`
- `Component.OpenJDK`
- `Microsoft.Component.ClickOnce.MSBuild`
- `Microsoft.Component.MSBuild`
- `Microsoft.Component.NetFX.Native`
- `Microsoft.Component.VC.Runtime.UCRTSDK`
- `Microsoft.Net.Component.4.6.1.TargetingPack`
- `Microsoft.Net.Component.4.6.TargetingPack`
- `Microsoft.Net.Component.4.7.2.TargetingPack`
- `Microsoft.Net.Component.4.8.SDK`
- `Microsoft.Net.Component.4.8.TargetingPack`
- `Microsoft.Net.ComponentGroup.4.8.DeveloperTools`
- `Microsoft.Net.ComponentGroup.DevelopmentPrerequisites`
- `Microsoft.Net.ComponentGroup.TargetingPacks.Common`
- `Microsoft.NetCore.Component.Runtime.10.0`
- `Microsoft.NetCore.Component.SDK`
- `Microsoft.VisualStudio.Component.CoreBuildTools`
- `Microsoft.VisualStudio.Component.DockerTools.BuildTools`
- `Microsoft.VisualStudio.Component.FSharp.MSBuild`
- `Microsoft.VisualStudio.Component.Node.Build`
- `Microsoft.VisualStudio.Component.NuGet`
- `Microsoft.VisualStudio.Component.NuGet.BuildTools`
- `Microsoft.VisualStudio.Component.Roslyn.Compiler`
- `Microsoft.VisualStudio.Component.Roslyn.LanguageServices`
- `Microsoft.VisualStudio.Component.SQL.SSDTBuildSku`
- `Microsoft.VisualStudio.Component.Sharepoint.BuildTools`
- `Microsoft.VisualStudio.Component.TeamOffice.BuildTools`
- `Microsoft.VisualStudio.Component.TestTools.BuildTools`
- `Microsoft.VisualStudio.Component.TextTemplating`
- `Microsoft.VisualStudio.Component.TypeScript.TSServer`
- `Microsoft.VisualStudio.Component.UWP.VC.ARM64`
- `Microsoft.VisualStudio.Component.UWP.VC.ARM64EC`
- `Microsoft.VisualStudio.Component.VC.ASAN`
- `Microsoft.VisualStudio.Component.VC.ATL`
- `Microsoft.VisualStudio.Component.VC.ATL.ARM64`
- `Microsoft.VisualStudio.Component.VC.ATL.ARM64.Spectre`
- `Microsoft.VisualStudio.Component.VC.ATL.Spectre`
- `Microsoft.VisualStudio.Component.VC.ATLMFC`

### codex/mailbox/VS_PRO_INSIDERS_ACTUAL_INSTALLED_20260218.vsconfig

- `Component.Android.NDK.R27C`
- `Component.Android.SDK.MAUI`
- `Component.Cocos`
- `Component.Linux.CMake`
- `Component.Linux.RemoteFileExplorer`
- `Component.MDD.Linux`
- `Component.Microsoft.NET.AppModernization`
- `Component.Microsoft.VisualStudio.LiveShare.2022`
- `Component.Microsoft.VisualStudio.RazorExtension`
- `Component.Microsoft.VisualStudio.Web.AzureFunctions`
- `Component.Microsoft.Web.LibraryManager`
- `Component.Microsoft.Windows.DriverKit`
- `Component.OpenJDK`
- `Component.UnityEngine.x64`
- `Component.Unreal`
- `Component.Unreal.Debugger`
- `Component.Unreal.Ide`
- `Component.VisualStudio.GitHub.Copilot`
- `ComponentGroup.Microsoft.NET.AppModernization`
- `Microsoft.Component.ClickOnce`
- `Microsoft.Component.CodeAnalysis.SDK`
- `Microsoft.Component.HelpViewer`
- `Microsoft.Component.MSBuild`
- `Microsoft.Component.NetFX.Native`
- `Microsoft.Component.PythonTools`
- `Microsoft.Component.PythonTools.Web`
- `Microsoft.Component.VC.Runtime.UCRTSDK`
- `Microsoft.ComponentGroup.Blend`
- `Microsoft.ComponentGroup.ClickOnce.Publish`
- `Microsoft.Net.Component.4.6.2.TargetingPack`
- `Microsoft.Net.Component.4.6.TargetingPack`
- `Microsoft.Net.Component.4.7.1.TargetingPack`
- `Microsoft.Net.Component.4.7.2.TargetingPack`
- `Microsoft.Net.Component.4.8.SDK`
- `Microsoft.Net.Component.4.8.TargetingPack`
- `Microsoft.Net.ComponentGroup.4.8.DeveloperTools`
- `Microsoft.Net.ComponentGroup.DevelopmentPrerequisites`
- `Microsoft.Net.ComponentGroup.TargetingPacks.Common`
- `Microsoft.NetCore.Component.DevelopmentTools`
- `Microsoft.NetCore.Component.Runtime.10.0`

