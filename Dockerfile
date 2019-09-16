FROM python:3.5-alpine

ADD dndice/ /dndice
ADD tests/ /tests

RUN pip install nose2

ENTRYPOINT [ "nose2", "--verbose" ]
