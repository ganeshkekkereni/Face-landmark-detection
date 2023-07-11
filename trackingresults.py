from xml.dom.minidom import getDOMImplementation, parse
import os
import os.path

class TrackingResults:

    def __init__(self):
        """constructor"""
        self.results = [] #results is a list of dicts
        self.imageSequence = None
        self.dimensions = {}
        self.templates = None
        self.frameValues = []

    def getResult(self, feature, frame):
        return self.results[frame][feature]

    def getFiltered(self, feature, idx, filterWidth = 5):
        filterWidth = int(filterWidth)

        samples = 0
        x = 0.0
        y = 0.0
        for i in xrange(-filterWidth/2, filterWidth/2+1):

            if 0 <= (idx+i) < len(self.results):
                x += self.results[idx+i][feature][0]
                y += self.results[idx+i][feature][1]
                samples += 1

        x /= samples
        y /= samples

        return (x,y)
        

    def load(self, filename):
        """loads the configuration from an xml file"""

        def handleFrame(frameNode):
            """handles a frame node"""

            def handleValue(valueNode, seq):
                name = str(valueNode.getAttributeNode("name").value)
                value = float((valueNode.getAttributeNode("value").value))
                self.frameValues[seq-1][name] = value


            def handleFeature(featureNode, seq):
                """handles a feature node"""
                featureId = str(featureNode.getAttributeNode("id").value)
                x = float(featureNode.getAttributeNode("x").value)
                y = float(featureNode.getAttributeNode("y").value)
#                print featureId
                self.results[seq-1][featureId] = [x,y]
            
            frameNumber = int(frameNode.getAttributeNode("seq").value)
            for child in frameNode.childNodes:
                if child.nodeType == child.ELEMENT_NODE:
                    if child.tagName == "feature":
                        handleFeature(child, frameNumber)

                    if child.tagName == "value":
                        handleValue(child, frameNumber)
                    
        def handleFeatureConfig(configNode):
            """handle a feature-config node"""

            def handleFeature(featureNode):
                """handle a feature node"""
                
                featureId = str(featureNode.getAttributeNode("id").value)
                width = int(featureNode.getAttributeNode("width").value)
                height = int(featureNode.getAttributeNode("height").value)
                self.dimensions[featureId] = [width, height]

            for child in configNode.childNodes:
                if child.nodeType == child.ELEMENT_NODE:
                    if child.tagName == "feature":
                        handleFeature(child)
                    
        def handleResults(resultNode):
            """handles a result node"""
            frameCount = int(resultNode.getAttributeNode("frame-count").value)
            self.results = []

            for i in xrange(frameCount):
                self.results.append({})
                self.frameValues.append({})
            
            try:
                self.imageSequence = str(resultNode.getAttributeNode("image-sequence").value)
            except:
                print "warning no image sequence found in results"
                pass


            for child in resultNode.childNodes:


                if child.nodeType == child.ELEMENT_NODE:
                    if child.tagName == "frame":
                        handleFrame(child)
                    if child.tagName == "feature-config":
                        handleFeatureConfig(child)
                    


                
        document = parse(filename)
        handleResults(document.getElementsByTagName("tracking-results")[0])

    # ___

    def checkConsistency(self):

        f = 0
        failure = False

        if self.results[f]["B"][0] < self.results[f]["A"][0]:
            print "right inner/outer consistency failure"
            failure = True

        if self.results[f]["A1"][0] < self.results[f]["B1"][0]:
            print "left inner/outer consistency failure"
            failure = True

        if self.results[f]["A1"][0] < self.results[f]["A"][0]:
            print "left/right eye consistency failure"
            failure = True

        if self.results[f]["H1"][0] < self.results[f]["H"][0]:
            print "left/right nostril consistency failure"
            failure = True


        if self.results[f]["K"][1] > self.results[f]["L"][1]:
            print "upper lower lip consistency failure"
            failure = True

        if self.results[f]["J"][0] < self.results[f]["I"][0]:
            print "left/right lip consistency failure"
            failure = True

        if self.results[f]["E1"][0] < self.results[f]["D1"][0]:
            print "left inner/outer brow consistency failure"
            failure = True

        if self.results[f]["D"][0] < self.results[f]["E"][0]:
            print "left inner/outer brow consistency failure"
            failure = True

        if self.results[f]["F"][1] > self.results[f]["G"][1]:
            print "right upper/lower eyelid consistency failure"
            failure = True

        if self.results[f]["F1"][1] > self.results[f]["G1"][1]:
            print "left upper/lower eyelid consistency failure"
            failure = True

        return not failure

    def save(self, filename):
        """saves the configuration to an xml file"""
   
        impl = getDOMImplementation()

        #create the results document
        resultsDoc = impl.createDocument(None, "tracking-results", None)
        topElement = resultsDoc.documentElement
        topElement.setAttribute("frame-count",`len(self.results)`)


        if self.imageSequence:
            topElement.setAttribute("image-sequence",str(self.imageSequence))

        #store the meta data
        metaDataElement = resultsDoc.createElement("meta-data")
        topElement.appendChild(metaDataElement)


        # in some cases we might not have the feature config :(
        if self.templates:
            featureConfigElement = resultsDoc.createElement("feature-config")
            for template in self.templates:
                featureElement = resultsDoc.createElement("feature")
                featureElement.setAttribute("id", str(template.id))
                featureElement.setAttribute("width", `template.dimensions[0]`)
                featureElement.setAttribute("height", `template.dimensions[1]`)
                featureConfigElement.appendChild(featureElement)
            topElement.appendChild(featureConfigElement)



        for frame in xrange(len(self.results)):

            lameFrame = frame+1
            frameElement = resultsDoc.createElement("frame")
            frameElement.setAttribute("seq", `lameFrame`)

            try:
                for key, value in self.frameValues[frame].iteritems():
                    valueElement = resultsDoc.createElement("value")
                    valueElement.setAttribute("name", str(key))
                    valueElement.setAttribute("value", `value`)
                    frameElement.appendChild(valueElement)
            except:
                pass
            

            for key, value in (self.results[frame].iteritems()):

                featureElement = resultsDoc.createElement("feature")
                featureElement.setAttribute("id", str(key))
                featureElement.setAttribute("x", `value[0]`)
                featureElement.setAttribute("y", `value[1]`)

                frameElement.appendChild(featureElement)

            topElement.appendChild(frameElement)

            

        text = resultsDoc.toprettyxml()
        d = os.path.dirname(filename)
        try:
            os.makedirs(d)
        except:
            pass
        
        outFile = file(filename,"wt")
        outFile.write(text)
        outFile.close()

    def setImageSequence(self, location):
        """sets the image sequence that was used during tracking"""
        self.imageSequence = location

    def getImageSequence(self):
        """returns the image sequence that was used during tracking"""
        return self.imageSequence    


    def getFrameCount(self):
        return len(self.results)


    def setTemplates(self, templates):
        """sets the templates, only used for saving"""
        self.templates = templates


    def clear(self, frameCount, featureCount):
        """clears the configuration"""
        self.imageSequence = None
        self.results = []
        

        for i in xrange(frameCount):
            self.results.append({})
            
