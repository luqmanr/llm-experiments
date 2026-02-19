#!/bin/bash
docker run --rm -it \
--name ocr \
--network host \
-v /home:/home \
-v $PWD/.paddlex:/root/.paddlex \
-w $(pwd) \
--entrypoint /bin/bash \
qimtronics/ocr:0.0.1-dev