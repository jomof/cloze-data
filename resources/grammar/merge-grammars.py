import sys

def main():
    if '--' not in sys.argv:
        print("Usage: merge_grammars.py <bunpro_files> -- <dojg_files>")
        sys.exit(1)
    
    split_index = sys.argv.index('--')
    
    bunpro_files = sys.argv[1:split_index]
    dojg_files = sys.argv[split_index+1:]
    
    print("Bunpro files:", bunpro_files)
    print("DOJG files:", dojg_files)

if __name__ == "__main__":
    main()
