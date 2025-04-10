# blockchain.py
class Blockchain:
    def __init__(self):
        self.chain = []

    def add_block(self, data):
        block = {"index": len(self.chain), "data": data}
        self.chain.append(block)

    def get_chain(self):
        return self.chain

blockchain = Blockchain()  # Singleton instance
