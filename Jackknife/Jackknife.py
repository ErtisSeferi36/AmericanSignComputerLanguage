import FeedData as fd
from functools import cmp_to_key
import numpy as np
import math
from JkBlades import JkBlades
from Vector import Vector
from JkTemplate import JkTemplate
from JkTemplate import compare_templates
from JkFeatures import JkFeatures
import mathematics
import random as r


# Add "JackknifeTemplate" object with parameters "blades" and "sample"
# Add "JackknifeFeatures" with parameters "blades" and "trajectory"
# Terms:
# Trajectory is the incoming data stream from our camera feed
GPSR_N = 6
GPSR_R = 2
BETA = 1.00


class Jackknife:
    def __init__(self, blades=JkBlades(), templates=fd.assemble_templates()):
        self.blades = blades
        self.templates = []
        for ii, t in enumerate(templates):
            t = mathematics.flatten(t)
            self.add_template(sample = t, id = ii % 5)
        self.length  = len(self.templates)
        self.train(GPSR_N, GPSR_R, BETA)
 
        
    
    def add_template(self, sample, id):
        self.templates.append(JkTemplate(self.blades, sample=sample, gid=id))

    def classify(self, trajectory):
        features = JkFeatures(self.blades, trajectory)
        template_cnt = int(len(self.templates))

        for t in self.templates:
            cf = 1.0

            if self.blades.cf_abs_distance:
                cf *= 1.0 / max(
                    0.01, np.dot(features.abs, t.features.abs)
                )

            if self.blades.cf_bb_widths:
                cf *= 1.0 / max(
                    0.01, np.dot(features.bb, t.features.bb)
                )
            
            t.cf = cf

            if self.blades.lower_bound:
                t.lb = cf * self.lower_bound(features.vecs, t)

            #TODO sort templates ???
            
        self.templates = sorted(self.templates, key=cmp_to_key(compare_templates))
        best = np.inf
        ret = -1

        for tt in range(0, template_cnt):

            if (self.templates[tt].lb > self.templates[tt].rejection_threshold):
                continue
            if (self.templates[tt].lb > best):
                continue

            score = self.templates[tt].cf

            score *= self.DTW(features.vecs, self.templates[tt].features.vecs)

            if (score > self.templates[tt].rejection_threshold):
                continue
            if (score < best):
                best = score
                ret = self.templates[tt].gesture_id
        
        return ret
    
    def train(self, gpsr_n, gpsr_r, beta):
        template_cnt = self.length
        distributions = []
        synthetic = []

        worst_score = 0.0

        for ii in range(0, 1000):

            for jj in range (0, 2):
                tt = math.floor(r.random() * template_cnt % template_cnt)

                s = self.templates[tt].sample
                length = len(s)

                print("line 99")
                print(length)

                start = math.floor(r.random() * (length / 2) % (length / 2))

                for kk in range(0, int(length/2)):
                    synthetic.append(s[start + kk]) 

            features = JkFeatures(self.blades, synthetic)

            for tt in range(0, template_cnt):
                score = self.DTW(features.vecs, self.templates[tt].features.vecs)
                print("Line 112")
                print(score)
                if (worst_score < score):
                    worst_score = score
                if (ii > 50):
                    distributions[tt].add_negative_score(score)
            
            if (ii != 50):
                continue
            
            for tt in range(0, template_cnt):
                distributions.append(Distributions(worst_score, 1000))
            
        
        for tt in range(0, template_cnt):
            for ii in range(0, 1000):
                synthetic = mathematics.gpsr(self.templates[tt].sample.trajectory, synthetic, gpsr_n, 0.25, gpsr_r)

                features = JkFeatures(self.blades, synthetic)
                score = self.DTW(features.vecs, self.templates[tt].features.vecs)
                distributions[tt].add_positive_score(score)

        for tt in range(0, template_cnt):
            threshold = distributions[tt].rejection_threshold(beta)
            self.templates[tt].rejection_threshold = threshold

    def DTW (self, v1, v2):

        cost = np.full((len(v1) + 1, len(v2) + 1), np.inf)
        cost[0][0] = 0.0

        print("JK 143 Printing cost matrix")
        for ii in range(1, len(v1)+1):
            for jj in range(max(1, ii - math.floor(self.blades.radius)), min(len(v2), ii + math.floor(self.blades.radius)) + 1):
                #dist = Vector.l2norm2(v1[i - 1], v2[j - 1])
                #TODO: Unknown if correct  
                cost[ii][jj] = min(min(cost[ii-1][jj], cost[ii][jj-1]), cost[ii-1][jj-1])
                
                print(str(ii) + " " + str(jj) + " " + str(cost[ii][jj]))
            if (self.blades.inner_product):
                cost[ii][jj] += 1.0 - np.dot(v1[ii - 1], v2[jj - 1])
            elif (self.blades.euclidean_distance):
                cost[ii][jj] += np.sum((v1[ii - 1] - v2[jj - 1]) ** 2)                
            else:
                assert(0)
        
        return cost[len(v1)][len(v2)]
    
    def lower_bound(self, vecs, template):
        lb = 0.0
        component_cnt = vecs.shape[1]  # Assuming vecs is a list of numpy arrays with shape [n_samples, n_features]
        for ii, vec in enumerate(vecs):
            cost = 0.0
            for jj in range(component_cnt):
                if self.blades.inner_product:
                    if vec[jj] < 0.0:
                        cost += vec[jj] * template.lower[ii][jj]
                    else:
                        cost += vec[jj] * template.upper[ii][jj]
                elif self.blades.euclidean_distance:
                    diff = 0.0
                    if vec[jj] < template.lower[jj]:
                        diff = vec[jj] - template.lower[ii][jj]
                    elif vec[jj] > template.upper[jj]:
                        diff = vec[jj] - template.upper[ii][jj]
                    cost += diff**2
                else:
                    raise ValueError("Invalid configuration for blades.")
            inner_prod = bool(self.blades.inner_product)
            if inner_prod:
                cost = 1.0 - min(1.0, max(-1.0, cost))

            lb += cost

        return lb


class Distributions:
    def __init__(self, max_score, bin_cnt):
        self.neg = np.zeros((bin_cnt), dtype='f')
        self.pos = np.zeros((bin_cnt), dtype='f')
        self.max_score = max_score

    def bin (self, score):
        print("JK 193 " + str(self.max_score))
        pt1 = math.floor(score * (len(self.neg) / self.max_score))
        pt2 = len(self.neg) - 1
        return min(pt1, pt2)
    
    def add_negative_score(self, score):
        self.neg[self.bin(score)] += 1

    def add_positive_score(self, score):
        self.pos[self.bin(score)] += 1

    def rejection_threshold(self, beta):

        self.neg = self.neg / (np.sum(self.neg))
        self.neg = np.cumsum(self.neg)
        assert(abs(self.neg[len(self.neg) - 1] - 1.0) < .00001)

        self.pos = self.pos / (np.sum(self.pos))
        self.pos = np.cumsum(self.pos)
        assert(abs(self.pos[len(self.pos) - 1] - 1.0) < .00001)

        alpha = 1.0 / (1.0 + beta * beta)
        precision = self.pos / (self.pos + self.neg)

        recall = self.pos

        best_score = 0.0
        best_idx = -1

        for ii in range(0, len(self.neg)):
            #might need fixing
            E = (alpha / precision[ii]) + ((1.0 - alpha) / recall[ii])
            f_score = 1.0 / E

            if (f_score > best_score):
                best_score = f_score
                best_idx = ii

        ret = best_idx + 0.5
        ret *= self.max_score / len(self.neg)
        
        return ret
    
j = Jackknife()
data = np.load('test.npy')
print(j.classify(data))