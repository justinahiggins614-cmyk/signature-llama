/* ============================================================
 * sigllama.d.ts — TypeScript definitions for Signature Llama.
 * Signature Llama: The Fully Cyber Utilizable AI
 * Independent model by Justin Addam Higgins. Not affiliated with Meta.
 *
 * Current model: SIGLLAMA-V2 (version 2.0), engine 1.0.
 * Covers: the SigLlama inference engine, the SignatureLlama site API
 * (llama-api.js), and the IndustryLlama cloud client (industry-llama.js).
 * Version 1.0 — 2026-10-03.
 * ============================================================ */

/** Named failure states. Never replaced by a generic "something went wrong". */
export type SigLlamaErrorCode =
  | 'ENGINE_LOAD_FAILED' | 'MODEL_NOT_FOUND' | 'MODEL_CORRUPT' | 'HASH_MISMATCH'
  | 'INVALID_MODEL' | 'INVALID_VOCAB' | 'BROWSER_UNSUPPORTED' | 'OUT_OF_MEMORY'
  | 'NETWORK_REQUIRED' | 'NETWORK_FAILED' | 'TIMEOUT' | 'GENERATION_TIMEOUT'
  | 'GENERATION_FAILED' | 'CONTEXT_TOO_LARGE' | 'INVALID_ARGUMENT'
  | 'MISSING_KEY' | 'BAD_KEY' | 'RATE_LIMITED' | 'NETWORK' | 'BAD_RESPONSE';

export interface SigLlamaError extends Error { code: SigLlamaErrorCode; }

/** Sampling options for SigLlama.generate(). */
export interface SigLlamaGenerateOptions {
  /** Maximum new tokens. Valid: positive integer. Default 120. */
  maxTokens?: number;
  /** Sampling temperature. temperature <= 0 = greedy argmax (deterministic).
   *  Valid: any finite number, typically 0–1.5. Default 0.8. */
  temperature?: number;
  /** Sample only from the K highest-scoring tokens.
   *  Valid: integer 1..vocab-1, else full vocab is used. Default 40. */
  topK?: number;
  /** Stop when the end-of-sequence token is sampled. Default true. */
  stopAtEos?: boolean;
  /** Called with each generated token string. */
  onToken?: (token: string) => void;
}

export interface SigLlamaModelInfo {
  params: number; vocab: number; dModel: number;
  layers: number; heads: number; seq: number;
}

/** The pure-JS inference engine (sigllama.js). Global `SigLlama`. */
export interface SigLlamaEngine {
  /** Load weights+vocab from a base URL. Defaults: vocabFile 'vocab.json',
   *  binFile 'sigllama-v1.bin' — pass 'vocab2.json' / 'sigllama-v2.bin'
   *  for SIGLLAMA-V2. Rejects with a named SigLlamaError. */
  load(baseUrl: string, vocabFile?: string, binFile?: string): Promise<SigLlamaModelInfo>;
  /** True when weights are parsed and the model is ready. */
  loaded(): boolean;
  /** Model facts, or null before load(). */
  info(): SigLlamaModelInfo | null;
  /** The vocabulary as a string array. */
  vocabList(): string[];
  /** True when the loaded vocab is word-level (v2), false for char-level (v1). */
  wordMode(): boolean;
  /** Encode text to token ids. */
  encode(text: string): number[];
  /** Decode token ids to text. */
  decode(ids: number[]): string;
  /** Generate text. Prompt is left-truncated to (context - maxTokens - 2). */
  generate(prompt: string, opts?: SigLlamaGenerateOptions): Promise<string>;
  /** Tool registry: tools register here via (new Function(lib.code))(). */
  tools: { [id: string]: any };
}

declare global {
  var SigLlama: SigLlamaEngine | undefined;
}

/** Every generated response carries this machine-readable provenance. */
export interface SigLlamaProvenance {
  ENGINE: string | null;
  MODEL_ID: string | null;
  MODEL_VERSION: string | null;
  MODE: 'trained_model' | 'guide' | 'industry' | 'failed';
  PROVIDER: 'local' | 'groq';
  LOCAL_OR_CLOUD: 'ON-DEVICE' | 'CLOUD' | 'N/A';
  TEMPERATURE: number | null;
  TOP_K: number | null;
  MAX_TOKENS: number | null;
  SEED: number | null;
  DETERMINISTIC: boolean;
  TIMESTAMP: string;
  PROVENANCE_STATUS: string;
  /** null when the trained model answered; otherwise one of:
   *  model-not-loaded | model-download-failed | unsupported-browser |
   *  corrupted-weights | engine-failure | quality-gate-rejected |
   *  user-asked-guide */
  FALLBACK_REASON: string | null;
}

export interface SigLlamaAnswer {
  answer: string;
  engine: string;
  mode: 'trained_model' | 'guide' | 'industry';
  model_id: string | null;
  model_version: string | null;
  provenance: SigLlamaProvenance;
}

/** Options for SignatureLlama.ask / askWithProvenance. */
export interface SignatureLlamaAskOptions extends SigLlamaGenerateOptions {
  /** When false and the model is not loaded, reject with MODEL_NOT_FOUND
   *  instead of answering from the knowledge base. Default true. */
  allowFallback?: boolean;
  /** Explicit trained-model-only answers (same as allowFallback:false).
   *  Default false. */
  requireModel?: boolean;
  /** Force temperature 0: greedy argmax, byte-identical replays. */
  deterministic?: boolean;
  /** Integer seed for reproducible sampling (mulberry32). */
  seed?: number;
  /** Reject with GENERATION_TIMEOUT after this many ms. */
  timeoutMs?: number;
}

/** The one-button reproducibility package (see manifest reproducibility_package). */
export interface SigLlamaReproPackage {
  prompt: string; seed: number | null; deterministic: boolean;
  temperature: number | null; topK: number | null; maxTokens: number | null;
  model_id: string | null; model_version: string | null;
  model_hash: string | null; engine_version: string; engine_hash: string;
  vocab_hash: string; output_hash: string; timestamp: string;
}

/** The on-demand site API (llama-api.js). Global `SignatureLlama`. */
export interface SignatureLlamaApi {
  version: string;
  site: string;
  modelId: 'SIGLLAMA-V2';
  modelVersion: '2.0';
  /** Pinned identity this API was released against. */
  pinned: {
    model_id: string; model_version: string;
    engine_sha256: string; weights_sha256: string; vocab_sha256: string;
    vocab_tokens: number; context_length: number;
  };
  /** 'trained' | 'guide' | 'loading' | 'failed' */
  mode(): string;
  /** Answer labeled with its engine identity. */
  ask(question: string, opts?: SignatureLlamaAskOptions): Promise<string>;
  /** Answer plus the full machine-readable provenance record. */
  askWithProvenance(question: string, opts?: SignatureLlamaAskOptions): Promise<SigLlamaAnswer>;
  /** Full-scale cloud Llama via Groq. NOT the on-device model.
   *  Rejects with MISSING_KEY when no key is saved. */
  askIndustry(question: string, opts?: { maxTokens?: number }): Promise<SigLlamaAnswer & { labeled: string }>;
  /** True when a cloud API key is saved in this browser. */
  industryReady(): boolean;
  /** Automatic integration proof: compares live model-status.json hashes
   *  with the pinned release. Use from the Telephone Book to verify the
   *  same engine+weights instead of trusting a typed claim. */
  verifyIntegration(): Promise<{
    ok: boolean; model_id: string; model_version: string;
    engine_hash_match: boolean; weights_hash_match: boolean; vocab_hash_match: boolean;
    engine_hash: string; weights_hash: string; vocab_hash: string; detail: string;
  }>;
  /** Build the reproducibility package for an askWithProvenance result. */
  reproPackage(result: SigLlamaAnswer, prompt?: string): SigLlamaReproPackage;
  /** Formal API surface names. */
  api: string[];
  /** All named error codes this API can produce. */
  errorCodes: SigLlamaErrorCode[];
}

/** Cloud model choices for Industry Standard mode. */
export interface IndustryLlamaModel {
  id: string; label: string; note: string;
}

/** The cloud client (industry-llama.js). Global `IndustryLlama`. */
export interface IndustryLlamaApi {
  models: IndustryLlamaModel[];
  endpoint: string;
  /** NOTE: returns the raw saved key. Never log it, never put it in a URL,
   *  transcript, or error report. */
  getKey(): string;
  setKey(key: string): void;
  getModel(): string;
  setModel(id: string): void;
  modelLabel(): string;
  getChoice(): 'v1' | 'industry';
  setChoice(c: 'v1' | 'industry'): void;
  ready(): boolean;
  chat(messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>,
       opts?: { maxTokens?: number; temperature?: number }): Promise<string>;
}

declare global {
  var SignatureLlama: SignatureLlamaApi | undefined;
  var IndustryLlama: IndustryLlamaApi | undefined;
}

export {};
