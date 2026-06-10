cbuffer PushConstants : register(b0)
{
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float4 layer_color;
};

struct VSInput
{
    float3 position : POSITION;
    float3 color : COLOR0;
};

struct VSOutput
{
    float4 position : SV_Position;
    float3 color : COLOR0;
    float2 uv : TEXCOORD0;
};

VSOutput main(VSInput input)
{
    VSOutput output;
    float4 world_pos = mul(model, float4(input.position, 1.0));
    float4 view_pos = mul(view, world_pos);
    output.position = mul(projection, view_pos);
    output.color = input.color;
    output.uv = world_pos.xy * 0.5 + 0.5;
    return output;
}
