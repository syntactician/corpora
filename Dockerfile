FROM ubuntu:xenial
ENV LC_ALL C.UTF-8
RUN apt-get update &&                     \
	apt-get install -y                \
		python3                   \
		python3-pip               \
		python3-boto              \
		python3-cookies           \
		python3-cssselect         \
		python3-bs4               \
		python3-future            \
		python3-fuzzywuzzy        \
		python3-levenshtein       \
		python3-lxml              \
		python3-nltk              \
		python3-responses         \
		python3-requests-oauthlib \
		python3-pydispatch        \
		python3-pymongo           \
		python3-queuelib          \
		python3-twisted           \
		python3-w3lib
RUN pip3 install         \
	chatterbot       \
	scrapy==1.1.0rc1 \
	vaderSentiment
