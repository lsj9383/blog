#include <iostream>

#include "google/protobuf/compiler/code_generator.h"
#include "google/protobuf/compiler/plugin.h"
#include "google/protobuf/compiler/plugin.pb.h"
#include "google/protobuf/descriptor.h"

class DemoGenerator : public google::protobuf::compiler::CodeGenerator {
 public:
  bool Generate(const google::protobuf::FileDescriptor* file, const std::string& parameter,
                google::protobuf::compiler::GeneratorContext* context,
                std::string* error) const override {
    error->append("========= IT IS A TEST ========");
    return false;
  }
};

int main(int argc, char* argv[]) {
  DemoGenerator generator;
  return google::protobuf::compiler::PluginMain(argc, argv, &generator);
}