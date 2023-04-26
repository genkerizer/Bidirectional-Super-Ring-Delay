docker run --rm -it \
		--net=host \
		--name=hopny \
		-v `pwd`/.:/hopny \
		quhu_gpu:2.2.0 bash