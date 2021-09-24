import json

import requests

from common import PathContextInformation
from pathlib import Path
import tempfile
import subprocess
import os

class JavaExtractor:
    def __init__(self, config, extractor_api_url, max_path_length, max_path_width):
        self.jar = Path('/hdd/code2seq/JavaExtractor/JPredict/target/JavaExtractor-0.0.1-SNAPSHOT.jar')
        self.config = config
        self.max_path_length = max_path_length
        self.max_path_width = max_path_width
        self.extractor_api_url = extractor_api_url
        self.bad_characters_table = str.maketrans('', '', '\t\r\n')

    def post_request(self, code_string):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        out = None
        try:
            tmp.write(bytes(code_string, encoding='utf-8'))
            command = f'java -cp {self.jar} JavaExtractor.App --max_path_length {self.max_path_length} --max_path_width {self.max_path_width} --file {tmp.name}'
            print(f'running {command}')
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            print(f'subprocess {out}')
        finally:
            if err:
                print(f'ERROR! PANIC! {err}')
            tmp.close()
            os.unlink(tmp.name)
        return out
        
        #return requests.post(url, data=json.dumps({"code": code_string, "decompose": True}, separators=(',', ':')))

    def extract_paths(self, code_string):
        response = self.post_request(code_string)
        response_array = json.loads(response)
        if 'errorType' in response_array:
            raise ValueError(response)
        if 'errorMessage' in response_array:
            raise TimeoutError(response)
        pc_info_dict = {}
        result = []
        for single_method in response_array:
            method_name = single_method['target']
            current_result_line_parts = [method_name]
            contexts = single_method['paths']
            for context in contexts[:self.config.DATA_NUM_CONTEXTS]:
                pc_info = PathContextInformation(context)
                current_result_line_parts += [str(pc_info)]
                pc_info_dict[(pc_info.token1, pc_info.shortPath, pc_info.token2)] = pc_info
            space_padding = ' ' * (self.config.DATA_NUM_CONTEXTS - len(contexts))
            result_line = ' '.join(current_result_line_parts) + space_padding
            result.append(result_line)
        return result, pc_info_dict
