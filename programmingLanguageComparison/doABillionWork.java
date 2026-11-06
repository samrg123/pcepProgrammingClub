class Main {
    static int doABillionWork(int val) {
        for(int i = 0; i < 1000000000; ++i) {
            val = (val+1) ^ val;
        }

        return val;
    }

    public static void main(String[] args){
        doABillionWork(5);
    }
}