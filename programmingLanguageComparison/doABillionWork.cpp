int doABillionWork(int val) {
    for(unsigned long long i = 0; i < 100'000'000'000ull; ++i) {
        val = (val+1) ^ val;
    }
    return val;
}

int main(int argc, const char** argv) {
    return doABillionWork(5);
}