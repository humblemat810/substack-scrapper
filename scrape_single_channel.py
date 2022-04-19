
import requests
from  matplotlib import pyplot as plt

test_ans = 24
debug_mode = False


def get_meta(base_url):
    i_oldest_article = 0
    oldest_response = []
    limit = 12
    ans = None
    def query( base_url, offset, limit=12 ):
        if debug_mode:
            return [{}] * min(limit, test_ans - offset) 
        uri = base_url + '/api/v1/archive?sort=new&search=&offset=' + str(offset) + '&limit=' + str(limit)
        print(uri)
        res = requests.get(uri)
        return res.json()
    
    i_head = 0
    interval = 2 * limit
    i_tail = i_head + interval
    
    res_head = query(base_url, i_head, limit)
    latest_post = res_head
    res_tail = query(base_url, i_tail, limit)
    l_head = len(res_head)
    l_tail = len(res_tail)
    i_mid = int((i_head + i_tail ) / 2)
    if (i_mid == i_head): # skip a query
        res_mid = res_head
        l_mid = l_head
    else:
        
        res_mid = query(base_url, i_mid, limit)
        l_mid = len(res_mid)
    
    print ("i_head:" , str(i_head), ", i_tail:",  str(i_tail) )
    
    
    cnt = 0
    found = False
    while not found :
        cnt += 1
        print( "iteration " + str(cnt))
        print ("i_head:" , str(i_head), ", i_tail:" , str(i_tail) + ', ')
        l_head = len(res_head)
        l_tail = len(res_tail)
        l_mid = len(res_mid)
        if l_tail > 0:
            if i_tail + l_tail > i_oldest_article:
                i_oldest_article =  i_tail + l_tail
                oldest_response = res_tail
        elif l_mid > 0:
            if i_mid + l_mid > i_oldest_article:
                i_oldest_article =  i_mid + l_mid
                oldest_response = res_mid
        elif l_head > 0:
            if i_head + l_head > i_oldest_article:
                i_oldest_article =  i_head + l_head
                oldest_response = res_head
        if i_head > 10000:
            print("err")
    
        if l_head < limit:  # this also covers the case when i_head is exactly the terminal, giving 0 length array
            print( "caught by head")
            if l_head > 0:
                oldest_response = res_head
            found = True
            ans = i_head + l_head
        elif l_mid < limit:
            if l_mid > 0:
                print( "caught by mid")
                ans = i_mid + l_mid
                found = True
            else:
                print( "located between i_head and mid")
                i_tail = i_mid
                res_tail = res_mid
                i_mid = int((i_head + i_tail ) / 2)
                if (i_mid == i_head): # skip a query
                    res_mid = res_head
                else:
                    res_mid = query(base_url, i_mid, limit)
                
        elif l_tail < limit:
            if l_tail > 0:
                print( "caught by tail")
                if l_tail > 0:
                    oldest_response = res_head
                ans = i_tail + l_tail
                found = True
            else:  # located between i_mid and tail
                print( "located between i_mid and tail")
                i_head = i_mid
                res_head = res_mid
                i_mid = int((i_head + i_tail ) / 2)
                if (i_mid == i_head): # skip a query
                    res_mid = res_head
                else:
                    res_mid = query(base_url, i_mid, limit)
                
        else:
            i_head = i_mid
            res_head = res_mid
            i_mid = i_tail
            res_mid = res_tail
    
            interval = interval * 2
            i_tail = i_head + interval
            res_tail = query(base_url, i_tail, limit)
            # extend tail this case
            print( "extend search range, i_head = " 
                  + str(i_head) + ", i_tail = " +  str(i_tail) 
                  + ", interval = " + str(interval))
    
    print( "number of article is ", ans)
    assert i_oldest_article == ans
    
    return ans, cnt, i_oldest_article, oldest_response[-1], latest_post[0]

if __name__ == '__main__':
    debug_mode = False
    if debug_mode:
        n_test = 400
        n_iteration = [-1] * n_test
        for i in range(n_test):
            test_ans = i
            acc_name = "milkkarten"
            base_url = 'https://'+acc_name+'.substack.com'
            n_article, cnt, i_oldest_article, oldest_response = get_meta(base_url)
            n_iteration[i] = cnt
            print("cnt = ", cnt)
            assert i == n_article
        plt.plot(n_iteration)
    acc_name = "milkkarten"
    base_url = 'https://'+acc_name+'.substack.com'
    n_article, cnt, i_oldest_article, oldest_response = get_meta(base_url)