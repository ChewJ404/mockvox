<div align="center">

<h1>🎤 MockVox</h1>

✨ Powerful Few-shot Voice Synthesis & Cloning Backend ✨<br><br>

**🇬🇧 English** | [**🇨🇳 简体中文**](./docs/cn/README.md)

</div>

---

## 🚀 Introduction

This project aims to build a community-driven voice synthesis & cloning platform.  
Adapted from [GPT_SoVITS](https://github.com/RVC-Boss/GPT-SoVITS), it maintains the same workflow while adding significant improvements.

🌟 **Core Features**:

1. **🎧 Zero-shot Text-to-Speech (TTS)**: Instant text-to-voice conversion with just a 5-second voice sample
2. **🌍 Cross-lingual Pipeline**: Full-cycle support for English/Japanese/Korean/Cantonese/Mandarin (training & inference)
3. **🧠 Few-shot TTS**: Fine-tune models with only 1 minute of training data for enhanced voice similarity and authenticity

🔧 **Key Enhancements**:

1. **🌐 Multilingual Architecture**
    * Implemented cross-lingual ​​training​​ (previously inference-only)
    * Language-specific BERT models for feature extraction
    * Enhanced inference robustness
2. **🖥️ CLI Interface**: Web UI replaced with flexible command-line operation [CLI Guide](./docs/en/cli.md)
3. **🏭 Distributed Architecture**: Celery-based multi-process async task scheduling for high concurrency
4. **⚡ Training Optimization**: Native PyTorch implementation replacing Pytorch Lightning
5. **🔊 ASR Upgrade**: NVIDIA Parakeet for English, latest ModelScope solutions for Japanese/Korean
6. **📦 Engineering Refinement**: Code restructuring and performance improvements

---

## 📥 Installation

### Clone Repository

```bash
git clone https://github.com/mockvox/mockvox.git
cd mockvox
```

---

## 🚀 Usage

### 🖥️ Local Deployment

#### 1. Create Virtual Environment

```bash
🐍 Create Python virtual environment
conda create -n mockvox python=3.11 -y
conda activate mockvox

📦 Install dependencies
pip install -e . 
```

#### 2. Copy .env

```bash
cp .env.sample .env
```

#### 3. Install FFmpeg

```bash
🎬 Ubuntu installation
sudo apt update && sudo apt install ffmpeg
ffmpeg -version  # Verify installation
```

#### 4. Download Pretrained Models

```bash
🔧 GPT-SoVITS Core Components
git clone https://huggingface.co/lj1995/GPT-SoVITS.git ./pretrained/GPT-SoVITS

🗣️ Voice Processing Suite
modelscope download --model 'damo/speech_frcrn_ans_cirm_16k' --local_dir './pretrained/damo/speech_frcrn_ans_cirm_16k' # Denoise
modelscope download --model 'iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch' --local_dir './pretrained/iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch' # Mandarin ASR
modelscope download --model 'iic/speech_fsmn_vad_zh-cn-16k-common-pytorch' --local_dir './pretrained/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch'
modelscope download --model 'iic/punc_ct-transformer_cn-en-common-vocab471067-large' --local_dir './pretrained/iic/punc_ct-transformer_cn-en-common-vocab471067-large' # Punctuation restoration
git clone https://huggingface.co/alextomcat/G2PWModel.git ./pretrained/G2PWModel # Grapheme-to-phoneme


🌐 Multilingual Extensions (Optional)
Skip if only using Chinese training data
modelscope download --model 'iic/speech_UniASR_asr_2pass-cantonese-CHS-16k-common-vocab1468-tensorflow1-online' --local_dir './pretrained/iic/speech_UniASR_asr_2pass-cantonese-CHS-16k-common-vocab1468-tensorflow1-online' # Cantonese ASR
git clone https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2.git ./pretrained/nvidia/parakeet-tdt-0.6b-v2 # English ASR
git clone https://huggingface.co/FacebookAI/roberta-large.git ./pretrained/FacebookAI/roberta-large # English BERT
modelscope download --model 'iic/speech_UniASR_asr_2pass-ja-16k-common-vocab93-tensorflow1-offline'  --local_dir './pretrained/iic/speech_UniASR_asr_2pass-ja-16k-common-vocab93-tensorflow1-offline' # Japanese ASR
git clone https://huggingface.co/tohoku-nlp/bert-large-japanese-v2.git ./pretrained/tohoku-nlp/bert-large-japanese-v2 # Japanese BERT
modelscope download --model 'iic/speech_UniASR_asr_2pass-ko-16k-common-vocab6400-tensorflow1-online' --local_dir './pretrained/iic/speech_UniASR_asr_2pass-ko-16k-common-vocab6400-tensorflow1-online' # Korean ASR
git clone https://huggingface.co/klue/roberta-large.git ./pretrained/klue/roberta-large # Korean BERT
```

Command-line interface is now ready for use.  [CLI Guide](./docs/en/cli.md)

#### 4. Start Services

For backend API operation:

```bash
🐳 Redis Container
chmod +x startup_redis.sh && ./startup_redis.sh
chmod +x check_redis.sh && ./check_redis.sh  # ✅ Status check

⚙️ Celery Worker Node
nohup celery -A src.mockvox.worker.worker worker --loglevel=info --pool=prefork --concurrency=1 &

🌐 Web Service
nohup python src/mockvox/main.py &
```

For API usage details, refer to the [API User Guide](./docs/en/api.md).

### 🐳 Docker Deployment

#### Using GPU within Docker Containers (Python/PyTorch)​​

To utilize NVIDIA GPUs from within Docker containers for Python/PyTorch applications, it is ​​essential​​ to install the ​​NVIDIA Container Toolkit​​ on the ​​bare-metal host​​ machine.

This toolkit provides the necessary drivers and runtime components to expose host GPU resources to containers. For detailed installation instructions and system requirements, please refer to the [NVIDIA Container Toolkit official guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

```bash
docker-compose up -d # 🚢 Launch full-stack services
```

**Note**​​: The default Docker image comes with the full language packages. To install Mandarin/English/Japanese/Korean/Cantonese versions, modify the MODEL_TYPE variable in the docker-compose.yml file.

---

## 🔍 Additional Notes

- 📁 All models are stored in `./pretrained` by default
- ⚠️ Initial run requires ~15GB model downloads
- 🔄 Modify `.env` for service configuration
- 📚 Complete CLI, API reference: [CLI Guide](./docs/en/cli.md) or [API User Guide](./docs/en/api.md)

---

<div align="center">
  <sub>Built with ❤️ by MockVox Team | 📧 Contact: dev@mockvox.cn</sub>
</div>
