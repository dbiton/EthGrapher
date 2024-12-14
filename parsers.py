from typing import Dict, List, Set, Tuple
import networkx as nx

def hex_to_bytes(s: str) -> bytes:
    if isinstance(s, str) and s.startswith("0x"):
        try:
            s = s[2:]
            if len(s) % 2 == 1:
                s = '0' + s
            return bytes.fromhex(s)
        except ValueError:
            raise ValueError(f"Invalid hexadecimal key: {s}")
    return s

def bytes_to_hex(b: bytes) -> bytes:
    if isinstance(b, bytes):
        hex = b.hex()
        while hex[0] == "0" and len(hex) > 1:
            hex = hex[1:]
        return '0x' + hex
    return b

def apply_recursively(obj, f):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            # Process the key
            key = f(key)
            new_dict[key] = apply_recursively(value, f)
        return new_dict
    elif isinstance(obj, list):
        return [apply_recursively(item, f) for item in obj]
    else:
        return f(obj)

def create_conflict_graph(txs: List[str], reads: Dict[str, Set[str]], writes: Dict[str, Set[str]]) -> nx.Graph:
    G = nx.Graph()

    G.add_nodes_from(txs)
    
    for tx0_hash, tx0_writes in writes.items():
      for tx1_hash, tx1_reads in reads.items():
        if tx0_hash != tx1_hash:
          if not tx0_writes.isdisjoint(tx1_reads):
            G.add_edge(tx0_hash, tx1_hash)
      for tx1_hash, tx1_writes in reads.items():
        # checks both tx0_hash != tx1_hash and removes redundent checks with >
        if tx0_hash > tx1_hash:
          if not tx0_writes.isdisjoint(tx1_writes):
            G.add_edge(tx0_hash, tx1_hash)

    return G

def parse_preStateTracer_trace(block_trace_diffFalse: dict, block_trace_diffTrue: dict) -> Tuple[Dict[str, Set[str]],Dict[str, Set[str]]]:
    writes: Dict[str, Set[str]] = {}
    reads: Dict[str, Set[str]] = {}
    
    for entry in block_trace_diffTrue:
        tx = entry["result"]
        tx_hash = entry["txHash"]
        tx_writes = set(tx['pre'])
        tx_writes.update(set(tx['post']))
        if len(tx_writes) > 0:
          writes[tx_hash] = tx_writes
    
    for entry in block_trace_diffFalse:
        tx = entry["result"]
        tx_hash = entry["txHash"]
        tx_reads = set(tx).difference(writes.get(tx_hash, set()))
        if len(tx_reads) > 0:
          reads[tx_hash] = set(tx).difference(writes.get(tx_hash, set()))
    
    return reads, writes


def parse_callTracer_trace_calls(call, reads, writes, inherited_prems):
    # CALLTYPE, RF, WF, RT, WT
    calls_prems = {
        "CALL":[True,False,True,True],
        "DELEGATECALL":[True,True,True,False],
        "CALLCODE":[True,True,True,False],
        "CREATE":[True,True,False,True],
        "CREATE2":[True,True,False,True],
        "STATICCALL":[True,False,True,False],
        "SELFDESTRUCT":[True,False,False,True],
        "SUICIDE":[True,False,False,True],
        "INVALID":[False,False,False,False],
        "REVERT":[False,False,False,False],
    }
    
    call_type = call["type"]
    prems = [p0 and p1 for (p0, p1) in zip(calls_prems[call_type], inherited_prems)]
    from_addr = call["from"]
    to_addr = call["to"]
    
    if prems[0]:
        reads.add(from_addr)
    if prems[1]:
        writes.add(from_addr)
    if prems[2]:
        reads.add(to_addr)
    if prems[3]:
        writes.add(to_addr)

    elif call_type == "SELFDESTRUCT":
        reads.add(call["from"])

    else:
        raise Exception(f"unhandled call type {call_type}!")

    if "calls" in call:
        for sub_call in call["calls"]:
            parse_callTracer_trace_calls(sub_call, reads, writes, writes_disabled)


def parse_callTracer_trace(block_trace):
    writes: Dict[str, Set[str]] = {}
    reads: Dict[str, Set[str]] = {}

    for entry in block_trace:
        tx = entry["result"]
        tx_hash = entry["txHash"]
        if "calls" in tx:
            for call in tx["calls"]:
                iter_reads = set()
                iter_writes = set()
                parse_callTracer_trace_calls(call, iter_reads, iter_writes, False)
                if tx_hash not in writes:
                    writes[tx_hash] = iter_writes
                else:
                    writes[tx_hash].update(iter_writes)
                if tx_hash not in reads:
                    reads[tx_hash] = iter_reads
                else:
                    reads[tx_hash].update(iter_reads)
    return reads, writes

def has_field(tx, field):
    return field in tx and tx[field] != b'' and tx[field] != None

def is_smart_contract_deployment(tx):
    return has_field(tx, "input") and not has_field(tx, 'to')

def is_smart_contract_interaction(tx):
    return has_field(tx, "input") and has_field(tx, 'to')