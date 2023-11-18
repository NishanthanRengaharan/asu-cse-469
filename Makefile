all: bchoc

bchoc: bchoc.py
    chmod +x bchoc.py
    ln -sf bchoc.py bchoc

clean:
    rm -f bchoc