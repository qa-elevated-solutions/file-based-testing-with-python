import sys
import json
import subprocess

def main():
    if len(sys.argv) < 2:
        return
    
    input_data = sys.argv[1]
    
    # Try JSON first
    try:
        parsed = json.loads(input_data)
        print(json.dumps(parsed, separators=(', ', ': ')))
        return
    except:
        pass
    
    # If it's a print statement or Python code, execute it
    if 'print(' in input_data or any(keyword in input_data for keyword in ['import ', 'def ', 'class ', 'for ', 'while ', 'if ']):
        try:
            result = subprocess.run(
                ['python', '-c', input_data],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(result.stdout.strip())
            return
        except:
            pass
    
    # Try math evaluation
    try:
        result = eval(input_data)
        print(result)
        return
    except:
        pass
    
    # Default: just echo
    print(input_data)

if __name__ == '__main__':
    main()