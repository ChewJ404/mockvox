#!/bin/bash

set -e  # 出现错误立即退出
set -o pipefail  # 管道命令错误退出

chmod +x /mockvox/Docker/baseDownload.sh
/mockvox/Docker/baseDownload.sh general
python /mockvox/Docker/generalDownload.py
# 安装中文模型文件
if [ "$MODEL_TYPE" == "full" ]; then
	/mockvox/Docker/baseDownload.sh english
	python /mockvox/Docker/cantoneseDownload.py
	/mockvox/Docker/baseDownload.sh japanese
	python /mockvox/Docker/japaneseDownload.py
	/mockvox/Docker/baseDownload.sh korean
	python /mockvox/Docker/koreanDownload.py
elif [ "$MODEL_TYPE" == "en" ]; then
	/mockvox/Docker/baseDownload.sh english
elif [ "$MODEL_TYPE" == "can" ]; then
	python /mockvox/Docker/cantoneseDownload.py
elif [ "$MODEL_TYPE" == "ja" ]; then
	/mockvox/Docker/baseDownload.sh japanese
	python /mockvox/Docker/japaneseDownload.py
elif [ "$MODEL_TYPE" == "ko" ]; then
	/mockvox/Docker/baseDownload.sh korean
	python /mockvox/Docker/koreanDownload.py
fi


cd /mockvox
# 确保文件存在
touch .env.sample
cp .env.sample .env
# 删除文件中的redis密码配置
sed -i '/^REDIS_PASSWORD=/d' .env 2>/dev/null
echo >> .env
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env
# 删除文件中的redis ip配置
sed -i '/^REDIS_HOST=/d' .env 2>/dev/null
echo >> .env
echo "REDIS_HOST=$REDIS_HOST" >> .env
if [ "$REDIS_PORT" != "" ]; then
	sed -i '/^REDIS_PORT=/d' .env 2>/dev/null
	echo >> .env
	echo "REDIS_PORT=$REDIS_PORT" >> .env
fi

mkdir -p /mockvox/log
nohup celery -A src.mockvox.worker.worker worker --loglevel=info --pool=prefork --concurrency=1 > log/celery.log 2>&1 &
nohup python src/mockvox/main.py > log/main.log 2>&1 &