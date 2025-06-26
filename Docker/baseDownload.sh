
language = $1
echo "Downloading $language models..."

base_url = "https://hf-mirror.com"
if [ "$MODEL_SOURCE" == "hr_mirror" ]; then
    base_url = "https://huggingface.co"
fi

cp /mockvox/Docker/$language.txt /mockvox/Docker/$language.template
input_file="/mockvox/Docker/$language.txt"

# 使用sed替换模板中的占位符
sed "s|{base_url}|$base_url|g" /mockvox/Docker/$language.template

aria2c --disable-ipv6 --input-file "/mockvox/Docker/$language.template" --dir /mockvox --continue