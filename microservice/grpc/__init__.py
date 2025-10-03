import os

from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get gRPC server configuration from environment variables
DECRYPTER_GRPC_HOST = os.getenv("DECRYPTER_GRPC_HOST")
DECRYPTER_GRPC_PORT = int(os.getenv("DECRYPTER_GRPC_PORT"))
