import zmq
import sys
import time

GTW_IP = "172.19.141.255"
PORT_REQ = 5555
PORT_SUB = 5556

def test_connection():
    context = zmq.Context()
    print(f"[*] Target GTW: {GTW_IP}")
    
    # Test REQ
    print(f"[1/2] Testing REQ Socket ({PORT_REQ})...")
    socket_req = context.socket(zmq.REQ)
    socket_req.setsockopt(zmq.RCVTIMEO, 2000)
    socket_req.setsockopt(zmq.LINGER, 0)
    try:
        socket_req.connect(f"tcp://{GTW_IP}:{PORT_REQ}")
        socket_req.send_string("HEARTBEAT")
        print(f"    <- Received: {socket_req.recv_string()}")
        print("    ✅ REQ SUCCESS")
    except Exception as e:
        print(f"    ❌ REQ Error: {e}")
    finally:
        socket_req.close()

    # Test SUB
    print(f"[2/2] Testing SUB Socket ({PORT_SUB})...")
    socket_sub = context.socket(zmq.SUB)
    socket_sub.setsockopt(zmq.RCVTIMEO, 5000)
    socket_sub.connect(f"tcp://{GTW_IP}:{PORT_SUB}")
    socket_sub.subscribe("")
    try:
        socket_sub.recv_string() # topic
        print(f"    <- Received Tick: {socket_sub.recv_string()}")
        print("    ✅ SUB SUCCESS")
    except Exception as e:
        print(f"    ❌ SUB Error: {e}")
    finally:
        socket_sub.close()
        context.term()

if __name__ == "__main__":
    test_connection()
