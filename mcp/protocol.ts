export interface MCPRequest {
  jsonrpc: "2.0";
  id?: number | string;
  method: string;
  params?: Record<string, any>;
}

export interface MCPResponse {
  jsonrpc: "2.0";
  id: number | string;
  result?: any;
  error?: { code: number; message: string };
}

export const ok = (id: number | string, result: any): MCPResponse => ({
  jsonrpc: "2.0",
  id,
  result,
});

export const fail = (id: number | string, message: string, code = -32603): MCPResponse => ({
  jsonrpc: "2.0",
  id,
  error: { code, message },
});
