export interface MCPRequest {
  id: number | string;
  method: string;
  params?: Record<string, any>;
}

export interface MCPResponse {
  id: number | string;
  result?: any;
  error?: { code: number; message: string };
}

export const ok = (id: number | string, result: any): MCPResponse => ({
  id,
  result,
});

export const fail = (id: number | string, message: string): MCPResponse => ({
  id,
  error: { code: -32603, message },
});
