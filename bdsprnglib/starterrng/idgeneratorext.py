from ..rng.xorshift import Xorshift

def generate_id(rng:Xorshift):
	raw = rng.get_rand()
	return (raw, raw % 1_000_000)