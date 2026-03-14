# TTHRESH Assessment: Tensor Compression via Tucker/HOSVD

## TL;DR
TTHRESH is a C++ lossy compressor for N-dimensional scientific grid data using Higher-Order SVD (Tucker decomposition) + bit-plane arithmetic coding. It achieves best-in-class rate-distortion at low bit rates but is 10-100x slower than competitors (SZ3, ZFP). A JAX rewrite is the right call — not PyTorch — for three reasons: native vmap/pmap for batched SVDs, XLA compilation for the entropy coding pipeline, and JAX is already the ecosystem standard for tensor decompositions (TensorLy-JAX, tntorch is PyTorch but focused on tensor trains).

## 1. What TTHRESH Does

**Paper:** Ballester-Ripoll, Lindstrom, Pajarola — "TTHRESH: Tensor Compression for Multidimensional Visual Data" (IEEE TVCG 2020)

**Pipeline:**
1. **HOSVD** — Unfold tensor along each mode, eigendecompose the Gram matrix, project to get core + N factor matrices
2. **Bit-plane quantization** — Encode core coefficients MSB→LSB, stop when target error (RMSE/PSNR/relative) is met
3. **Entropy coding** — RLE + arithmetic coding on bit-plane streams

**Key properties:**
- Non-local: every coefficient touches every voxel (unlike wavelet/DCT block methods)
- Smooth degradation without blocking artifacts at extreme compression ratios
- Fine-grained bit-rate control via bit-plane truncation
- Supports in-domain operations: crop, downsample, slice from compressed representation

**Benchmarks vs competitors:**
| | TTHRESH | SZ3 | ZFP |
|---|---|---|---|
| Rate-distortion (low BR) | Best | Good | Good |
| Speed | 10-100x slower | Fast | Fast |
| Artifacts | Smooth | Varies | Blocky |
| Random access | No | No | Yes |
| Scalability | Limited (OOM on large data) | Excellent | Excellent |

## 2. Implementation Analysis

**Language:** C++ (Eigen for linalg, zlib, optional OpenMP)

**Architecture strengths:**
- Clean separation: tucker.hpp (HOSVD) → compress.hpp (quantization) → encode.hpp (entropy)
- Vendored Eigen, minimal dependencies
- OpenMP parallelization of unfolding/projection

**Architecture weaknesses:**
- Sequential mode processing in HOSVD (modes processed one at a time)
- Full materialization of unfolding matrices → memory-bound for large tensors
- Arithmetic coder is inherently sequential (hard to parallelize)
- No GPU path at all
- No batching — single tensor at a time
- No gradient/autodiff for learned compression extensions

## 3. Rewrite Recommendation: JAX (not PyTorch)

### Why JAX over PyTorch

| Factor | JAX | PyTorch |
|---|---|---|
| Batched SVD/eigendecomp | `jax.vmap` over modes — trivial | Manual batching, less elegant |
| XLA compilation | `jax.jit` compiles full pipeline including control flow | `torch.compile` improving but less mature for non-NN workloads |
| Tensor decomposition ecosystem | TensorLy backend, emerging standard | tntorch exists but TT-focused |
| Parallelism model | `pmap`/`shard_map` for multi-device | DistributedDataParallel (NN-centric) |
| Functional purity | Natural fit for mathematical transforms | Stateful paradigm adds friction |
| Custom kernels | Pallas for entropy coding on TPU/GPU | CUDA extensions (more boilerplate) |

### Why NOT PyTorch
- PyTorch's strength is neural network training loops. TTHRESH is a **mathematical transform pipeline** — no parameters to learn in the base algorithm.
- tntorch (Ballester-Ripoll's own PyTorch library) already covers tensor train decompositions. Duplicating in PyTorch competes with his own work.
- JAX's functional style maps directly to the HOSVD algebra: pure functions, no side effects, composable transformations.

### What a JAX rewrite unlocks
1. **GPU-accelerated HOSVD** — The eigendecomposition bottleneck moves to cuSOLVER/XLA
2. **Batched compression** — `vmap` over a batch of tensors trivially
3. **Differentiable compression** — `jax.grad` through the Tucker decomposition enables learned compression (optimize factor matrices end-to-end)
4. **TPU support** — Free via XLA, useful for large-scale scientific data
5. **JIT-compiled entropy coding** — While arithmetic coding is sequential, the bit-plane extraction and RLE can be vectorized

## 4. Research Directions

### Direction A: Differentiable Tucker Compression (HIGH IMPACT)
Replace HOSVD with learned factor matrices optimized end-to-end for rate-distortion. The HOSVD gives optimal factors for MSE, but:
- Real error metrics (SSIM, perceptual, topology-preserving) are non-MSE
- Joint optimization of quantization + factor matrices can beat sequential HOSVD→quantize
- **JAX enables this naturally** via `jax.grad` through the full pipeline
- Related: neural image compression (Balle et al.) but for N-dimensional scientific data

### Direction B: Streaming/Progressive Tucker (MEDIUM-HIGH IMPACT)
TTHRESH's biggest practical limitation is no streaming. Research direction:
- Hierarchical Tucker (H-Tucker) decomposition for progressive refinement
- Block-Tucker hybrid: local Tucker blocks with global coordination
- Enables partial decompression and random access while preserving non-local quality
- Direct competition with ZFP's random-access advantage

### Direction C: Adaptive Rank Selection (MEDIUM IMPACT)
Current TTHRESH uses bit-plane truncation for rate control but fixed-rank HOSVD. Research:
- Data-dependent rank selection per mode (some modes compress better than others)
- Bayesian rank estimation (automatic rank via ARD priors)
- Connection to tensor completion / low-rank recovery literature

### Direction D: Tucker + Neural Residual Coding (HIGH IMPACT, TRENDY)
Hybrid approach:
1. Tucker decomposition captures global structure
2. Small neural network codes the residual (what Tucker can't represent)
3. Combines TTHRESH's smooth degradation with neural flexibility
- Related to COIN/COIN++ (neural field compression) but with explicit tensor structure
- JAX makes this natural: Tucker is a pure function, neural residual is a Flax/Haiku module

### Direction E: Topology-Preserving Tucker Compression (MEDIUM IMPACT, NICHE)
Recent work (2025) shows augmenting TTHRESH with topological constraints yields best compression ratios among topology-preserving methods. Research:
- Integrate persistent homology constraints directly into the Tucker optimization
- Differentiable topology loss (via persistence diagram differentiability)
- Important for scientific visualization where features must be preserved

### Direction F: Multi-resolution Tucker for Climate/Weather Data (HIGH IMPACT, APPLIED)
Climate data (ERA5, CMIP6) is massive, multidimensional, and needs lossy compression:
- Spatio-temporal Tucker decomposition with physical priors
- Mode-specific compression: spatial modes compress well, temporal modes less so
- Integration with Zarr/NetCDF ecosystem
- Benchmark against SZ3 and MGARD on real climate datasets

## 5. Proposed Scope for a JAX Rewrite

### Phase 1: Core (2-3 weeks)
- `jax_tthresh.tucker`: HOSVD via `jnp.linalg.svd` + mode unfolding
- `jax_tthresh.quantize`: Bit-plane quantization with target error
- `jax_tthresh.entropy`: Simplified entropy coding (skip arithmetic coder initially, use zlib)
- Parity test: compress/decompress same datasets as C++ version, compare PSNR

### Phase 2: Differentiable (2-3 weeks)
- End-to-end differentiable Tucker compression
- Custom `jax.grad`-compatible quantization (straight-through estimator or soft quantization)
- Learned factor matrices via gradient descent
- Benchmark: rate-distortion improvement over vanilla HOSVD

### Phase 3: Scale (2-3 weeks)
- Multi-GPU via `pmap` for large tensors
- Streaming/progressive variant
- Zarr/NetCDF I/O integration
- Benchmark against SZ3, ZFP, SPERR on standard scientific datasets

## 6. Key References

- Ballester-Ripoll et al., "TTHRESH: Tensor Compression for Multidimensional Visual Data" (IEEE TVCG 2020)
- Ballester-Ripoll, "tntorch: Tensor Network Learning with PyTorch" (JMLR 2022)
- Kossaifi et al., "TensorLy: Tensor Learning in Python" (JMLR 2019)
- Balle et al., "Variational Image Compression with a Scale Hyperprior" (ICLR 2018) — for learned compression ideas
- Underwood et al., "Augmenting Lossy Compressors with Topological Guarantees" (2025)
- Li et al., "SPERR: Lossy Scientific Data Compression" (IPDPS 2023)

## 7. Verdict

**Rewrite in JAX. Don't rewrite in PyTorch.**

The value proposition is not just "GPU-accelerated TTHRESH" (that alone is incremental). The real opportunity is **differentiable tensor compression** — a research direction that JAX enables naturally and that doesn't exist yet. The combination of Tucker's mathematical elegance with end-to-end gradient-based optimization for scientific data compression is unexplored territory with high publication potential.

Start with Direction A (differentiable Tucker) as the core contribution, use Direction F (climate data) as the application domain, and Direction D (neural residual) as the stretch goal.
