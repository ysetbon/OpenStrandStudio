import cProfile

def main():
    # Your existing code
    pass

if __name__ == "__main__":
    cProfile.run('main()', filename='profiling_results.prof')
