// @SID: FORGE_CSHARP_CONTRACTS_V1
// Purpose: C# class contracts mirrored from recovered TypeScript declarations.
using System.Collections.Generic;

namespace ChthonicArchive.Forge.Recovered;

public sealed class PrismBandContract
{
    public Dictionary<string, object?> Snapshot { get; init; } = new();
}

public sealed class TopologyNodeContract
{
    public string Path { get; init; }
    public string Prism_band { get; init; }
}

public sealed class TopologyDataContract
{
    public double Nodes_count { get; init; }
    public double Edges_count { get; init; }
    public string Generated { get; init; }
    public List<object?> Nodes { get; init; }
}

public sealed class DependencyGraphContract
{
    public Dictionary<string, object?> Snapshot { get; init; } = new();
}

public sealed class ExecCaptureResultContract
{
    public string Stdout { get; init; }
    public string Stderr { get; init; }
    public object? Error { get; init; }
}

public sealed class MoveViewFnContract
{
    public Dictionary<string, object?> Snapshot { get; init; } = new();
}

public sealed class DevKitReportContract
{
    public string Msys2_home { get; init; }
    public string Ucrt64_bin { get; init; }
    public string Perl_path { get; init; }
    public string Cc { get; init; }
    public string Cxx { get; init; }
    public string Env_vars { get; init; }
    public string Path_prepend { get; init; }
}

public sealed class ProposedApiFnContract
{
    public Dictionary<string, object?> Snapshot { get; init; } = new();
}

