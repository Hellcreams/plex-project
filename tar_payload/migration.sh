#!/bin/bash

# 지역 변수
source_dir=./USB/
target_dir=./Device/
scan_dir=0


# 실행 스크립트
mkdir "$target_dir"/temp
cp "$source_dir"*.tar "$target_dir"/temp --update=none
cd "$target_dir"/temp

for archive in *.tar; do
	tar -xvkf "$archive"
	arch_dir="${archive%.tar}" &&
	mv -n "$arch_dir" ../ >/dev/null 2>&1 &&
		echo New : "$arch_dir" ||
		echo Error or Duplicated : "$arch_dir"
done

cd ..
rm -r ./temp

# 스크립트 새로고침
curl "http://127.0.0.1:32400/library/sections/all/refresh"
