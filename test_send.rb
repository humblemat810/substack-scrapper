
require 'uri'
require 'net/http'
require 'json'
limit = 12
def query( offset, limit)
    uri = URI('https://milkkarten.substack.com/api/v1/archive?sort=new&search=&offset=' + offset.to_s + '&limit=' + limit.to_s)
    puts uri
    res = Net::HTTP.get_response(uri)
    return JSON.parse(res.body)
end
i_head = 0
interval = 2 * limit
i_tail = i_head + interval
res_head = query(i_head, limit)
res_tail = query(i_tail, limit)
l_head = res_head.length
l_tail = res_tail.length
i_mid = Integer((i_head + i_tail ) / 2)
if (i_mid == i_head) # skip a query
    res_mid = res_head
    l_mid = l_head
else
    
    res_mid = query(i_mid, limit)
    l_mid = res_mid.length
end
print "i_head:" 
print i_head.to_s
print ", i_tail:" 
print i_tail.to_s
puts


cnt = 0
found = false
while not found
    puts "iteration " + cnt.to_s
    cnt = cnt + 1
    if cnt > 10
        break
    end
    print "i_head:" 
    print i_head.to_s
    print ", i_tail:" 
    print i_tail.to_s + ', '
    l_head = res_head.length
    l_tail = res_tail.length
    l_mid = res_mid.length
    

    if l_head < limit  # this also covers the case when i_head is exactly the terminal, giving 0 length array
        puts "caught by head"
        found = true
        ans = i_head + l_head
    elsif l_mid < limit
        if l_mid > 0
            put "caught by mid"
            ans = i_mid + l_mid
            found = true
        else
            puts "located between i_head and mid"
            i_tail = i_mid
            res_tail = res_mid
            i_mid = Integer((i_head + i_tail ) / 2)
            if (i_mid == i_head) # skip a query
                res_mid = res_head
            else
                res_mid = query(i_mid, limit)
            end
        end
    elsif l_tail < limit
        if l_tail > 0
            puts "caught by tail"
            ans = i_tail + l_tail
            found = true
        else  # located between i_mid and tail
            puts "located between i_mid and tail"
            i_head = i_mid
            res_head = res_mid
            i_mid = Integer((i_head + i_tail ) / 2)
            if (i_mid == i_head) # skip a query
                res_mid = res_head
            else
                res_mid = query(i_mid, limit)
            end
        end
    
    else
        i_head = i_mid
        res_head = res_mid
        i_mid = i_tail
        res_mid = res_tail

        interval = interval * 2
        i_tail = i_head + interval
        res_tail = query(i_tail, limit)
        # extend tail this case
        puts "extend search range, i_head = " + i_head.to_s + ", i_tail = " +  i_tail.to_s + ", interval = " + interval.to_s
    end
end
puts "number of article is " + ans.to_s