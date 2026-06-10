cbuffer PushConstants : register(b0)
{
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float4 layer_color;
};

struct PSInput
{
    float4 position : SV_Position;
    float3 color : COLOR0;
    float2 uv : TEXCOORD0;
};

float4 main(PSInput input) : SV_Target
{
    float2 grid_uv = input.uv * 32.0;
    float2 grid_fract = abs(frac(grid_uv) - 0.5) * 2.0;
    float min_dist = min(grid_fract.x, grid_fract.y);
    float line_intensity = saturate((0.02 - min_dist) * 50.0);
    float3 spectral = layer_color.rgb;
    float3 final_color = lerp(input.color, spectral, 0.7);
    final_color = lerp(final_color, float3(1.0, 1.0, 1.0), line_intensity * 0.2);
    return float4(final_color, 1.0);
}
