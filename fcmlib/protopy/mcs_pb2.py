# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: mcs.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tmcs.proto\x12\x07protopy\"\x85\x02\n\x0cLoginRequest\x12\n\n\x02id\x18\x01 \x02(\t\x12\x0e\n\x06\x64omain\x18\x02 \x02(\t\x12\x0c\n\x04user\x18\x03 \x02(\t\x12\x10\n\x08resource\x18\x04 \x02(\t\x12\x12\n\nauth_token\x18\x05 \x02(\t\x12\x11\n\tdevice_id\x18\x06 \x01(\t\x12\x1e\n\x16received_persistent_id\x18\n \x03(\t\x12\x1a\n\x12\x61\x64\x61ptive_heartbeat\x18\x0c \x01(\x08\x12\x37\n\x0c\x61uth_service\x18\x10 \x01(\x0e\x32!.protopy.LoginRequest.AuthService\"\x1d\n\x0b\x41uthService\x12\x0e\n\nANDROID_ID\x10\x02\"B\n\rLoginResponse\x12\n\n\x02id\x18\x01 \x02(\t\x12\x0b\n\x03jid\x18\x02 \x01(\t\x12\x18\n\x10server_timestamp\x18\x08 \x01(\x03\"%\n\x07\x41ppData\x12\x0b\n\x03key\x18\x01 \x02(\t\x12\r\n\x05value\x18\x02 \x02(\t\"\xec\x02\n\x0b\x44\x61taMessage\x12\n\n\x02id\x18\x02 \x01(\t\x12\x0c\n\x04\x66rom\x18\x03 \x02(\t\x12\n\n\x02to\x18\x04 \x01(\t\x12\x10\n\x08\x63\x61tegory\x18\x05 \x02(\t\x12\r\n\x05token\x18\x06 \x01(\t\x12\"\n\x08\x61pp_data\x18\x07 \x03(\x0b\x32\x10.protopy.AppData\x12\x1b\n\x13\x66rom_trusted_server\x18\x08 \x01(\x08\x12\x15\n\rpersistent_id\x18\t \x01(\t\x12\x11\n\tstream_id\x18\n \x01(\x05\x12\x1f\n\x17last_stream_id_received\x18\x0b \x01(\x05\x12\x0e\n\x06reg_id\x18\r \x01(\t\x12\x16\n\x0e\x64\x65vice_user_id\x18\x10 \x01(\x03\x12\x0b\n\x03ttl\x18\x11 \x01(\x05\x12\x0c\n\x04sent\x18\x12 \x01(\x03\x12\x0e\n\x06queued\x18\x13 \x01(\x05\x12\x0e\n\x06status\x18\x14 \x01(\x03\x12\x10\n\x08raw_data\x18\x15 \x01(\x0c\x12\x15\n\rimmediate_ack\x18\x18 \x01(\x08')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'mcs_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _LOGINREQUEST._serialized_start=23
  _LOGINREQUEST._serialized_end=284
  _LOGINREQUEST_AUTHSERVICE._serialized_start=255
  _LOGINREQUEST_AUTHSERVICE._serialized_end=284
  _LOGINRESPONSE._serialized_start=286
  _LOGINRESPONSE._serialized_end=352
  _APPDATA._serialized_start=354
  _APPDATA._serialized_end=391
  _DATAMESSAGE._serialized_start=394
  _DATAMESSAGE._serialized_end=758
# @@protoc_insertion_point(module_scope)
