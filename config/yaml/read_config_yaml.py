import yaml

class ReadConfigYaml(object):
    def __init__(self, yaml_file_path):
        self.yaml_file_path = yaml_file_path

    def read_yaml(self):
        """
        读取 YAML 配置文件
        :return: 解析后的 YAML 数据
        """
        try:
            with open(self.yaml_file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"文件 {self.yaml_file_path} 未找到")
            return None
        except Exception as e:
            print(f"读取 YAML 文件时出错: {e}")
            return None