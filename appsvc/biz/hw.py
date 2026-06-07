from enum import StrEnum


class GpuModel(StrEnum):
    INTEL_UHD_P630 = "intel-uhd-p630"  # RISE-3
    INTEL_UHD_750 = "intel-uhd-750"  # PC-CUSTOM-1
    NVIDIA_GTX_1060 = "nvidia-gtx-1060"  # PC-CUSTOM-1
    NVIDIA_TESLA_V100S = "nvidia-tesla-v100s"  # OVH t2-*
    NVIDIA_L4 = "nvidia-l4"  # OVH l4-*
