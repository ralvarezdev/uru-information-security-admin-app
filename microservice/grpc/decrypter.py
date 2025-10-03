import grpc

import ralvarezdev.decrypter_pb2_grpc as decrypter_pb2_grpc

def create_grpc_client(host: str, port: int):
    """
    Creates and returns a gRPC client stub.

	Args:
		host (str): The server host.
		port (int): The server port.

	Returns:
		decrypter_pb2_grpc.DecrypterStub: The gRPC client stub.
    """
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = decrypter_pb2_grpc.DecrypterStub(channel)
    return stub