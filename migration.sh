#!/bin/bash

# 지역 변수
source_dir=./USB/
target_dir=./Device/
scan_dir=0

# 오류 처리


# 실행 스크립트
cp "$source_dir"*.tar "$target_dir" --update=none

cd "$target_dir"
for archive in *.tar; do
	if tar -xvkf "$archive"; then
		echo tar is in
		movie_dir="${archive%.tar}"
	fi
	rm "$archive"
done
