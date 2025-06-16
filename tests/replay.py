import json

def process_sse_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
        current_event = None
        current_data = None
        for line in f_in:
            line = line.strip()
            if line.startswith('event:'):
                # If we have a previous event and data, check if it has content
                if current_event and current_data:
                    try:
                        data_dict = json.loads(current_data)
                        if current_event != "message_chunk" or (current_event == "message_chunk" and data_dict.get('content')):
                            f_out.write(f"event: {current_event}\n")
                            f_out.write(f"data: {current_data}\n\n")
                    except json.JSONDecodeError:
                        pass
                current_event = line[6:].strip()
                current_data = None
            elif line.startswith('data:'):
                current_data = line[5:].strip()
        # Process the last event and data
        if current_event and current_data:
            try:
                data_dict = json.loads(current_data)
                if 'content' in data_dict:
                    f_out.write(f"event: {current_event}\n")
                    f_out.write(f"data: {current_data}\n\n")
            except json.JSONDecodeError:
                pass

if __name__ == "__main__":
    input_file = r"D:/github/deer-flow/web/public/replay/PChgXnVKPyRSg7epbqbGS.txt"
    output_file = r"D:/github/deer-flow/web/public/replay/PChgXnVKPyRSg7epbqbGS-2.txt"
    process_sse_file(input_file, output_file)
