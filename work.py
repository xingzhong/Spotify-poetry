# -*- coding: utf-8 -*-

import requests
import re
import numpy as np

class track(dict):
    # inheritance dict for easy debug 
    def __init__(self,*arg,**kw):
        super(track, self).__init__(*arg, **kw)
    def __repr__(self):
        return "'%s'"%self['name'].encode("utf-8")
    
class spotify(object):
    def __init__(self):
        url = "https://api.spotify.com/v1/search"
        self._req = lambda x: requests.get(url, params={"q":"\"%s\""%x, "type":'track', "limit":1})
        self._cache = {}
        self._chart = {}
        self._ignore = []
        self._c = 1
        
    def req(self, q):
        # request to spotify $q$ is the query string
        q = " ".join(q)
        if q in self._cache: return self._cache[q]  
        # memory cache every request's response. 
        # 
        for k,v in self._cache.iteritems():
            if (k in q) and v['tracks']['total'] == 0:  
            # trick 1: if the substring $k$ has no response,
            # then string $q$ will also have no response.
                return v
            if (q in k) and v['tracks']['total'] > 0:
            # trick 2: if the string $k$ has response,
            # then it's substring will guarantee have response
                return v

        r = self._req(q)
        self._c += 1
        if r.status_code == 200:
            self._cache[q] = r.json()
            print "[debug %s %s] req : q = %s"%(self._c, self._cache[q]['tracks']['total'], q)
        else:
            self._cache[q] = None
        return self._cache[q]
    
    def render(self):
        # render a spotify playlist for convenience 
        uris = map(lambda x:x['id'], self._tracks[0])
        tpl = "<iframe src='https://embed.spotify.com/?uri=spotify:trackset:PREFEREDTITLE:{0}'></iframe>"
        return tpl.format(",".join(uris))
    
    def query(self, msg):
        # pre-process the query, 
        # return playlists and its loss
        self._ignore = []
        msg = re.sub("[!\"#$%&'()*+,./:;<=>?@\^_`{|}~-]", '', msg)
        self._tokens = msg.split()
        self._tracks = self._query(0, len(self._tokens))
        return self._tracks, self.measure(map(lambda x:x['name'], self._tracks[0]))
    
    def _query(self, i, j):
        # trick 3: 
        # recursive tree hashmap 
        #   _query[i, j] denotes 'optimum' solition for substring s[i:j]
        #   top-down fashion, so initial call will be _query (0 , len(s))
        if (i, j) in self._chart:
            # mem cache
            return self._chart[(i, j)]
        else:
            # for any new sub string s[i:j], 
            # first check whether s[i,j] do match single track
            
            r = self.req(self._tokens[i:j])
            if r['tracks']['total'] > 0: 
                # if match, then save as optimum 
                self._chart[(i, j)] = ([track(r['tracks']['items'][0])], self._tokens[i:j], 1)

            elif i+1 == j:
                # if this is single work token, and no matching results, 
                # then should throw error, because there is impossible to build result
                # here we append this word to self._ignore 
                # and using "unknown" to replace this ill word.
                print "[error]", self._tokens[i:j]
                self._ignore.append(self._tokens[i:j])
                r = self.req(['unknown'])
                self._chart[(i, j)] = ([track(r['tracks']['items'][0])], ['unknown'], 1)

            else:
                # the entire substring do not match any result
                # so we split it into two subsubstring, hope the subsubstring can match
                # split to two piece will yield a binary tree structure. 
                # ideally if the error metric have dynamic properties, e.g. optimal substructure
                # then the two optimum branches should yield optimum tree. 
                # here, we do not have this property, so this is a heuristic method  
                # it can not guarantee optimum solution.
                minNum, argMin = 1e10, i+1
                rg = range(i+1, j)
                rgs = sorted(rg, key=lambda x : (x-rg[(j-i-1)/2])**2 )
                # rgs is the list of k index 
                # I rearrange this list.
                # The index which seperates the list into half will have pirority

                for k in rgs:
                    # k is the split index for s[i:j] -> s[i:k], s[k,j]
                    # recursive find optimum for each branch
                    self._chart[(i, k)] = self._query(i, k)
                    self._chart[(k, j)] = self._query(k, j)
                    # count the total num of tracks in tree as the heuristoc value.
                    numTrack = self._chart[(i, k)][-1] + self._chart[(k, j)][-1]
                    if numTrack < minNum:
                        minNum = numTrack
                        argMin = k

                #sort and find the best in heuristic space.
                self._chart[(i, j)] = (self._chart[(i,argMin)][0] + self._chart[(argMin,j)][0], minNum)
            
            # return mem cached optimum value
            return self._chart[(i, j)]
    
        
    def measure(self, tracks, alpha=1.0, beta=1.0):
        return alpha * len(tracks) +  beta *len(tracks)*np.var( map(lambda x:len(x.split()), tracks) )
    
if __name__ == '__main__':
    s = spotify()
    #q = s.query(u"Nonetheless, we are slowly but surely getting through all your submissions. \
    #    Whilst we can’t put them all online, we do read every single one you send us, \
    #    so please keep them coming!")
    query = s.query(u"if i can't let it go xingzhong")
    print query
