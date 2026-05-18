#include <cuda_runtime.h>

#include <cstdio>

__global__ void write_probe(int* output) {
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        output[0] = 4090;
    }
}

int main() {
    int* device_value = nullptr;
    int host_value = 0;

    cudaError_t status = cudaMalloc(&device_value, sizeof(int));
    if (status != cudaSuccess) {
        std::fprintf(stderr, "cudaMalloc failed: %s\n", cudaGetErrorString(status));
        return 1;
    }

    write_probe<<<1, 1>>>(device_value);
    status = cudaDeviceSynchronize();
    if (status != cudaSuccess) {
        std::fprintf(stderr, "kernel launch failed: %s\n", cudaGetErrorString(status));
        cudaFree(device_value);
        return 2;
    }

    status = cudaMemcpy(&host_value, device_value, sizeof(int), cudaMemcpyDeviceToHost);
    if (status != cudaSuccess) {
        std::fprintf(stderr, "cudaMemcpy failed: %s\n", cudaGetErrorString(status));
        cudaFree(device_value);
        return 3;
    }

    std::printf("cuda_probe=%d\n", host_value);
    cudaFree(device_value);
    return 0;
}
