iSo there is the simple python script that meant to be placed to /usr/lib/cgi-bin on your Pi (don't forget to do chmod +x) and called from ISY like this:
 
To close: http://1.1.1.1/cgi-bin/myq-cgi.py?user=user@example.com&pass=secret1&cmd=close
To open: http://1.1.1.1/cgi-bin/myq-cgi.py?user=user@example.com&pass=secret1&cmd=open

If you want to test the script:
http://1.1.1.1/cgi-bin/myq-cgi.py?user=user@example.com&pass=secret1&cmd=status

It currently does not support 2 openers on the same account but that is fairly easy to add if there is a demand for it (I have a 2 car garage but it's only one door).
