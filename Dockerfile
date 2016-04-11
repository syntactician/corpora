FROM ubuntu
RUN apt-get update &&                        \
	apt-get install -y                   \
		python3                      \
		python3-pip                  \
		python3-w3lib                \
		python3-twisted-experimental \
		libxml2-dev                  \
		libxslt1-dev                 \
		libz-dev
RUN pip3 install scrapy==1.1.0rc1
