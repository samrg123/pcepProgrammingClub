import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.GridLayout;
import java.awt.Rectangle;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Random;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.swing.BoxLayout;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.WindowConstants;

public class Main {

    public static class Neuron {
        protected double[] m_weights;
        
        public Neuron(double[] weights) {
            m_weights = weights.clone();
        }

        public Neuron(int inputSize, Random random) {
            // Note: +1 for bias
            m_weights = random.doubles(inputSize+1, -1, 1).toArray();
        }

        public double Eval(double[] inputs, int inputOffset) {
            // TODO: compare ReLu / tanh / sigmoid
            
            // initialize to bias
            int biasIndex = m_weights.length-1;
            double weightedInput = m_weights[biasIndex];

            for(int i = 0; i < biasIndex; ++i) {
                weightedInput+= inputs[inputOffset + i] * m_weights[i];
            }

            // THIS is super slow, but converges a lot better
            return Math.tanh(weightedInput);

            // // leaky reLU
            // return (weightedInput < 0) ? (.01 * weightedInput) : weightedInput;
        }
    }   

    public static class Layer {
        protected Neuron[] m_neurons;
        protected double[] m_results;

        protected int m_inputSize;

        public Layer(int inputSize, Neuron[] neurons) {
            m_inputSize = inputSize;
            m_neurons = neurons.clone();
            m_results = new double[neurons.length];
        }

        public Layer(int inputSize, int outputSize, Random random) {
            m_inputSize = inputSize;
            m_neurons = new Neuron[outputSize];
            m_results = new double[outputSize];

            for(int i = 0; i < outputSize; ++i) {
                m_neurons[i] = new Neuron(inputSize, random);
            }            
        }

        public void Eval(double[] inputs, int inputOffset, double[] outputs, int outputOffset) {
            assert outputs.length >= m_neurons.length : ("Invalid input size: "+inputs.length+" | Expected at least: "+m_neurons.length);

            for(int i = 0; i < m_neurons.length; ++i) {
                outputs[outputOffset + i] = m_neurons[i].Eval(inputs, inputOffset);
            }
        }

        public double[] Eval(double[] inputs) {
            Eval(inputs, 0, m_results, 0);
            return m_results;
        }
    }

    public static class Network {
        protected Layer[] m_layers;
        
        protected int m_inputSize;
        protected int m_outputSize;
        protected int m_maxNumLayerWeights;

        protected static class ThreadState {
            public double[] input;
            public double[] output;
            public double[] hiddenLayerBuffer;

            public ThreadState(Network network) {
                input  = new double[network.m_inputSize];
                output = new double[network.m_outputSize];

                // Note: hiddenLayerBuffer needs to be large enough to store input and output partial results
                //       really we could just use this for all inputs / output, but we have other
                //       arrays to size them correctly to match network dimensions
                hiddenLayerBuffer = new double[2*network.m_maxNumLayerWeights];
            }
        }

        ThreadLocal<ThreadState> m_threadState = ThreadLocal.withInitial(() -> new ThreadState(this));

        public Network(int inputSize, int[] layerWidths, Random random) {

            int numLayers = layerWidths.length;
            assert numLayers > 0: "Invalid numLayers. Expected pos number got: "+numLayers;

            m_layers = new Layer[numLayers];
            m_inputSize = inputSize;
            m_outputSize = layerWidths[numLayers-1];
            
            // Note: updated below;
            m_maxNumLayerWeights = inputSize;

            // create layers
            int layerInputSize = inputSize;
            for(int i = 0; i < numLayers; ++i) {
                int layerWidth = layerWidths[i];
                m_layers[i] = new Layer(layerInputSize, layerWidth, random);
            
                if(layerWidth > m_maxNumLayerWeights) {
                    m_maxNumLayerWeights = layerWidth;
                }

                layerInputSize = layerWidth;
            }
        }

        public void Reset(Random random) {
            for(Layer layer : m_layers) {
                for(Neuron neuron : layer.m_neurons) {
                    neuron.m_weights = random.doubles(neuron.m_weights.length, -1, 1).toArray();
                }
            }
        }

        public double[] Eval(double[] inputs) {        
            for(Layer layer : m_layers) {
                inputs = layer.Eval(inputs);
            }
            
            return inputs;
        }

        public ThreadState GetThreadState() {
            return m_threadState.get();
        }

        public double[] EvalThreadSafe(ThreadState threadState) {            
            double[] inputs  = threadState.input;
            double[] results = threadState.output;
            double[] outputs = threadState.hiddenLayerBuffer;
            
            // eval intermediate layers into outputs
            // Note: we offset the input and output because we cannot call Eval with same input and output location.
            //       If we did input will be partially overwritten during neuron eval calls
            int inputReadOffset = 0;
            int outputWriteOffset = 0;
            int lastLayerIndex = m_layers.length - 1;

            for(int i = 0; i < lastLayerIndex; ++i) {
                Layer layer = m_layers[i];
                
                layer.Eval(inputs, inputReadOffset, outputs, outputWriteOffset);
            
                inputs = outputs;
                inputReadOffset = outputWriteOffset;
                outputWriteOffset = (outputWriteOffset == 0) ? m_maxNumLayerWeights : 0;
            }

            // eval output layer into correctly sized results array
            m_layers[lastLayerIndex].Eval(inputs, inputReadOffset, results, 0);       
            return results;
        }
    }

    public static class NetworkPanel extends JPanel {
        public String m_name;

        public Font m_font = new Font("consolas", Font.PLAIN, 12);

        public Network  m_network;
        public String[] m_inputNames;
        public String[] m_outputNames;
        public Color[]  m_outputColors;

        public double m_namePadding = 5;
        public Color  m_nameColor   = Color.GRAY;

        public double m_neuronRadius  = 12.5;            
        public double m_neuronPadding = 10 + m_neuronRadius;
        public double m_layerPadding  = 20 + m_neuronRadius;
        public double m_biasLength    = m_neuronPadding / 2;

        // Note: tmp variable for RGB to HSV color conversion... Java Color library is slow and dumb
        private float[] m_tmpHSV = new float[3];

        public NetworkPanel(String name, Network network, String[] inputNames, String[] outputNames, Color[] outputColors) {
            m_name         = name;
            m_network      = network;
            m_inputNames   = inputNames;
            m_outputNames  = outputNames;
            m_outputColors = outputColors;                 
        }

        @Override
        public void paint(Graphics graphics) {

            Dimension panelSize = getSize();
            Rectangle bounds = new Rectangle(0, 0, panelSize.width, panelSize.height);

            graphics.setColor(Color.BLACK);
            graphics.fillRect(bounds.x, bounds.y, bounds.width, bounds.height);

            graphics.setFont(m_font);
            FontMetrics fontMetrics = graphics.getFontMetrics();

            // draw name
            int nameWidth = fontMetrics.stringWidth(m_name);
            int nameX = bounds.x + (int)(m_namePadding + .5 * (bounds.width - nameWidth - m_namePadding));
            int nameY = bounds.y + (int)(m_namePadding + fontMetrics.getHeight());

            graphics.setColor(m_nameColor);
            graphics.drawString(m_name, nameX, nameY);


            if(m_network == null) return;

            int neuronDiameter = (int)(2 * m_neuronRadius);
            int numLayers = m_network.m_layers.length;

            double layerXOffset = bounds.x + m_layerPadding;
            double layerYOffset = bounds.y + m_neuronPadding;
            
            double layerHeight = bounds.height - 2*m_neuronPadding;
            double layerStride = (double)(bounds.width - 2*m_layerPadding) / numLayers;

            // Note: the normalized significance of each neuron in a layer relative to each final output neuron
            //       we preallocate a significance array bit enough to fit the output layer and the next computed input layer   
            //       and update relevant indices as needed. Values are initialized for a 1 hot encoding for last output layer
            int outputSize = m_network.m_outputSize;
            int significancesStride = m_network.m_maxNumLayerWeights * outputSize;
            double[] significances = new double[2 * significancesStride];
            for(int i = 0; i < outputSize; ++i) {
                significances[i*outputSize + i] = 1;
            };
            
            // Note: we draw layers in reverse order to allow us to backpropagate significance
            int outputLayerSignificanceOffset = 0;
            int lastLayerIndex = numLayers-1;
            for(int l = lastLayerIndex; l >= 0 ; --l) {
                boolean drawOutputNames = (m_outputNames != null && l == lastLayerIndex);
                
                Layer layer = m_network.m_layers[l];

                int numInputs = layer.m_inputSize;
                int numNeurons = layer.m_neurons.length;

                double inputStride = layerHeight / numInputs;
                double neuronStride = layerHeight / numNeurons; 

                int inputX = (int)(layerXOffset + l * layerStride);
                int neuronX = (int)(inputX + layerStride);

                double neuronYOffset = layerYOffset + .5*neuronStride;

                // zero initialize input significances
                int inputLayerSignificanceOffset = (outputLayerSignificanceOffset == 0) ? significancesStride : 0;
                int inputSignificanceSize = numInputs * outputSize;
                for(int i = 0; i < inputSignificanceSize; ++i) {
                    significances[inputLayerSignificanceOffset + i] = 0;
                }

                int lastNeuronIndex = numNeurons - 1; 
                for(int n = 0; n < numNeurons; ++n) {
                    Neuron neuron = layer.m_neurons[n];
                    int neuronY = (int)(neuronYOffset + n * neuronStride);

                    int neuronSignificanceOffset = outputLayerSignificanceOffset + n*outputSize;
                    Color neuronColor = GetNeuronColor(outputSize, neuronSignificanceOffset, significances, m_outputColors);
                    double neuronSignificance = neuronColor.getAlpha() / 255.0;

                    // compute weight magnitude for normalization
                    double totalAbsWeight = 0;
                    for(int i = 0; i < neuron.m_weights.length; ++i) {
                        totalAbsWeight+= Math.abs(neuron.m_weights[i]);
                    }
                    double absWeightNormalizer = (totalAbsWeight != 0) ? 1/totalAbsWeight : 1;

                    // draw inputs
                    for(int i = 0; i < numInputs; ++i) {
                        double inputYOffset = layerYOffset + .5*inputStride;
                        int inputY = (int)(inputYOffset + i * inputStride);

                        double weightSignificance = Math.abs(neuron.m_weights[i]) * absWeightNormalizer;
                        Color weightColor = GetWeightColor(weightSignificance, neuronColor, neuronSignificance);

                        graphics.setColor(weightColor);
                        graphics.drawLine(inputX, inputY, neuronX, neuronY);

                        // update input neuron significance
                        int inputSignificanceOffset = inputLayerSignificanceOffset + i*outputSize;
                        for(int o = 0; o < outputSize; ++o) {
                            double outputSignificance = significances[neuronSignificanceOffset + o];
                            significances[inputSignificanceOffset + o]+= outputSignificance * weightSignificance;
                        }

                        // Note: we draw inputs on lastNeuronIndex so we can colorize it to match significance
                        boolean drawInputNames = (m_inputNames != null && l == 0 && n == lastNeuronIndex);
                        if(drawInputNames) {
                            String inputName = m_inputNames[i];
                            int inputNameWidth = fontMetrics.stringWidth(inputName);

                            // center x
                            int inputNameX = inputX - inputNameWidth;
                            if(inputNameWidth < m_layerPadding) {
                                inputNameX-= (m_layerPadding - inputNameWidth)/2;
                            }

                            // center Y
                            int inputNameY = inputY + (fontMetrics.getAscent() - fontMetrics.getLeading())/2;

                            //Note: this gets called for last neuron input so we can safely compute the input layer color
                            Color inputNameColor = GetNeuronColor(outputSize, inputSignificanceOffset, significances, m_outputColors);
                            graphics.setColor(inputNameColor);
                            graphics.drawString(inputName, inputNameX, inputNameY);
                        }
                    }      

                    // draw neuron bias
                    double neuronBiasSignificance = Math.abs(neuron.m_weights[numInputs]) * absWeightNormalizer;
                    Color biasColor = GetWeightColor(neuronBiasSignificance, neuronColor, neuronSignificance);

                    int biasX1 = (int)(neuronX - .5*m_biasLength);
                    int biasX2 = (int)(neuronX + .5*m_biasLength);
                    int biasY1 = neuronY;
                    int biasY2 = (int)(neuronY + m_neuronRadius + m_biasLength);

                    graphics.setColor(biasColor);
                    graphics.drawLine(neuronX, biasY1, neuronX, biasY2);
                    graphics.drawLine(biasX1, biasY2, biasX2, biasY2);

                    // draw neuron
                    graphics.setColor(neuronColor);
                    
                    // Note: fillOval is upper left x,y coordinates NOT center
                    int neuronCornerX = (int)(neuronX - m_neuronRadius);
                    int neuronCornerY = (int)(neuronY - m_neuronRadius);
                    graphics.fillOval(neuronCornerX, neuronCornerY, neuronDiameter, neuronDiameter);

                    if(drawOutputNames) {                        
                        graphics.drawString(m_outputNames[n], neuronCornerX, neuronCornerY);
                    }
                }

                outputLayerSignificanceOffset = inputLayerSignificanceOffset;
            }
        }

        protected Color GetNeuronColor(int outputSize,int significanceOffset, double[] significances, Color[] outputColors) {

            int neuronR = 0;
            int neuronG = 0;
            int neuronB = 0;
            double neuronAlpha = 0;
            
            // compute neuron color with brightness of each output color based on output significance 
            for(int i = 0; i < outputSize; ++i) {
                double significance = significances[significanceOffset + i];
                
                Color outputColor = outputColors[i];
                Color.RGBtoHSB(outputColor.getRed(), outputColor.getGreen(), outputColor.getBlue(), m_tmpHSV);
                
                Color significanceColor = Color.getHSBColor(m_tmpHSV[0], m_tmpHSV[1], (float)significance);
            
                neuronR+= significanceColor.getRed();
                neuronG+= significanceColor.getGreen();
                neuronB+= significanceColor.getBlue();                
                
                neuronAlpha+= significance;
            }

            // normalize color to maximum dynamic range to keep everything visible
            int maxValue = (neuronR > neuronG) ? neuronR : neuronG;
            if(neuronB > maxValue) maxValue = neuronB;

            double normalizer = (maxValue != 0) ? (255./maxValue) : 1;

            neuronR*= normalizer;
            neuronG*= normalizer;
            neuronB*= normalizer;

            int neuronA = (neuronAlpha >= 1) ? 255 : 
                        (neuronAlpha <= 0) ? 0   : (int)(255 * neuronAlpha);

            return new Color(neuronR, neuronG, neuronB, neuronA);
        }

        protected Color GetWeightColor(double weightSignificance, Color neuronColor,  double neuronSignificance) {

            double weightAlpha = weightSignificance * neuronSignificance;

            int weightARGB = neuronColor.getRGB();
            weightARGB = (weightARGB & 0xFFFFFF) | ((int)(weightAlpha * 255) << 24);

            return new Color(weightARGB, true);
        }            
    };

    public static enum GraphMode {
        RESTART,
        WRAP,
        SCROLL
    }

    public static class GraphPanel extends JPanel {
        public String m_name = "Graph";
        public Color m_color = Color.GRAY;

        public Font m_font = new Font("consolas", Font.PLAIN, 12);
        public int m_padding = 5;

        public Color m_cursorColor  = Color.ORANGE;
        public boolean m_drawCursor = true;

        public double[] m_data;
        public int m_dataStartIndex = 0;
        public int m_dataEndIndex   = 0;
        public int m_cursorIndex    = 0;
        
        public GraphMode m_mode = GraphMode.RESTART;

        public int m_maxPoints;            

        public double m_yMin = 0;
        public double m_yMax = 1;

        public double m_xMin = 0;
        public double m_xMax = 1;                

        protected int[] m_pointsX;
        protected int[] m_pointsY;
        
        public GraphPanel(String name, int maxPoints, double[] data, int dataStartIndex, int dataEndIndex) {
            m_name      = name;
            m_maxPoints = maxPoints;

            m_data           = data;
            m_dataStartIndex = dataStartIndex;
            m_dataEndIndex   = dataEndIndex;
            m_cursorIndex    = m_dataStartIndex;

            m_pointsX = new int[maxPoints];
            m_pointsY = new int[maxPoints];
        }

        public int GetNumPoints() {
            return Math.min(m_maxPoints, m_dataEndIndex - m_dataStartIndex);
        }

        @Override
        public void paint(Graphics graphics) {
            Rectangle bounds = getBounds();

            // clear screen
            graphics.setColor(Color.BLACK);
            graphics.fillRect(0, 0, bounds.width, bounds.height);

            graphics.setColor(m_color);
                
            // draw title
            int fontSize = m_font.getSize();

            int    cursorX = m_cursorIndex - m_dataStartIndex;
            double cursorY = (m_dataEndIndex > m_dataStartIndex) ? m_data[m_cursorIndex] : 0;

            double yMin = m_yMin;
            double yMax = m_yMax;
            if(yMin > yMax) {
                yMin = 0;
                yMax = 0;
            }
            String graphTitle = String.format("%s [%.01f, %.01f]: (%d, %.01f)", m_name, yMin, yMax, cursorX, cursorY);                

            graphics.setFont(m_font);
            graphics.drawString(graphTitle, m_padding, fontSize);

            // draw x axis
            int xAxisY  = bounds.height - m_padding;
            int xAxisX1 = m_padding;
            int xAxisX2 = bounds.width - m_padding;
            graphics.drawLine(xAxisX1, xAxisY, xAxisX2, xAxisY);

            // draw y axis
            int yAxisX  = m_padding;
            int yAxisY1 = m_padding + fontSize;
            int yAxisY2 = bounds.height - m_padding; 
            graphics.drawLine(yAxisX, yAxisY1, yAxisX, yAxisY2);

            // draw points from data
            int xAxisLength = xAxisX2 - xAxisX1;
            int yAxisLength = yAxisY2 - yAxisY1;

            double xAxisRange = m_xMax - m_xMin;
            double yAxisRange = m_yMax - m_yMin;

            double xPixelStride = xAxisLength / xAxisRange;
            double yPixelStride = yAxisLength / yAxisRange;
            
            // only start scrolling the graph once we reach the end of it
            int numPoints = GetNumPoints();
            boolean scrollGraph = ((m_mode == GraphMode.SCROLL) && (numPoints == m_maxPoints));

            for(int i = 0; i < numPoints; ++i) {
                
                // scroll yIndex to keep poly line connected in right order
                int yIndex = m_dataStartIndex + (scrollGraph ? ((cursorX + 1 + i) % m_maxPoints) : i);
                                                        
                double yVal = m_data[yIndex];

                m_pointsX[i] = xAxisX1 + (int)(xPixelStride * i);
                m_pointsY[i] = yAxisY2 - (int)(yPixelStride * (yVal - m_yMin));
            }
            graphics.drawPolyline(m_pointsX, m_pointsY, numPoints);

            // draw cursor
            if(m_drawCursor) {
                graphics.setColor(m_cursorColor);

                int cursorDrawX = scrollGraph ? (numPoints - 1) : cursorX;
                int cursorPointX = xAxisX1 + (int)(xPixelStride * cursorDrawX);

                graphics.drawLine(cursorPointX, yAxisY1, cursorPointX, yAxisY2);
            }
        }

        public void pushPoint(double value, boolean scaleAxis) {
            if(scaleAxis) {
                if(value < m_yMin) {
                    m_yMin = value;
                }

                if(value > m_yMax) {
                    m_yMax = value;
                }
            }

            switch(m_mode) {

                case SCROLL:
                case WRAP: {
                    if(m_dataEndIndex < m_maxPoints) {
                        m_cursorIndex = m_dataEndIndex;
                        ++m_dataEndIndex;

                    } else if(++m_cursorIndex >= m_maxPoints) {
                        m_cursorIndex = 0;
                    }

                    m_data[m_cursorIndex] = value;
                } break;
                
                default: {
                    // RESTART
                    if(m_dataEndIndex >= m_maxPoints) {
                        m_dataEndIndex = 0;
                    }

                    m_cursorIndex = m_dataEndIndex;
                    m_data[m_dataEndIndex++] = value;

                } break;
            
            }
        }
    }

    public static class GraphPane extends JScrollPane {

        public JPanel m_viewportPanel = new JPanel();

        public GraphPane() {
            setViewportView(m_viewportPanel);

            setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER);
            setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);

            m_viewportPanel.setLayout(new BoxLayout(m_viewportPanel, BoxLayout.Y_AXIS));
        }        
    }


    // TODO: Split this up so we can draw each population individually
    //       ... or should we just use multiple windows?
    public static class NetworkGUI extends AppFrame {

        public static final int kDefaultWindowWidth = 700;
        public static final int kDefaultWindowHeight = 400;
        
        public static final int kDefaultGraphWidth  = (int)(kDefaultWindowWidth * .4 + .5);
        public static final int kDefaultGraphHeight = 50;

        protected GridLayout m_networkContainerLayout = new GridLayout(1,1);
        protected JPanel m_networkContainer = new JPanel(m_networkContainerLayout);

        protected GraphPane m_graphPane = new GraphPane();

        
        public NetworkGUI(String title) {
            super(title, kDefaultWindowWidth, kDefaultWindowHeight);

            m_contentPane.setLayout(new BoxLayout(m_contentPane, BoxLayout.X_AXIS));

            m_contentPane.add(m_networkContainer);
            m_contentPane.add(m_graphPane);

            m_networkContainer.setPreferredSize(new Dimension(kDefaultWindowWidth - kDefaultGraphWidth, kDefaultWindowHeight));
            m_graphPane.setPreferredSize(new Dimension(kDefaultGraphWidth, kDefaultWindowHeight));
        
            m_networkContainer.setBackground(Color.black);
            m_graphPane.setBackground(Color.black);
        }

        public NetworkPanel AddNetworkPanel(String name, Network network, String[] inputNames, String[] outputNames, Color[] outputColors) {
            NetworkPanel networkPanel = new NetworkPanel(name, network, inputNames, outputNames, outputColors);

            int numComponents = m_networkContainer.getComponentCount() + 1;
            int numRows = (int)(Math.sqrt(numComponents) + .5);

            m_networkContainerLayout.setRows(numRows);            
            m_networkContainer.add(networkPanel);

            return networkPanel;
        }

        public GraphPanel AddGraph(String name, int maxPoints, double data[], int startIndex, int endIndex) {
            GraphPanel graphPanel = new GraphPanel(name, maxPoints, data, startIndex, endIndex);
            graphPanel.setPreferredSize(new Dimension(kDefaultGraphWidth, kDefaultGraphHeight));

            m_graphPane.m_viewportPanel.add(graphPanel);

            return graphPanel;
        }
    };


    public static class GeneticAlgorithm {
        
        public static final Game.Direction[] kDirections = Game.Direction.values();

        public Network m_network;
        public Random m_random;

        protected static class ThreadState {
            public int[] sortedDirectionIndices;
            public Network.ThreadState networkThreadState;

            public ThreadState(GeneticAlgorithm geneticAlgorithm) {

                // TODO: can we just merge the network thread state to here?
                networkThreadState = geneticAlgorithm.m_network.GetThreadState();
                
                sortedDirectionIndices = new int[kDirections.length];
                for(int i = 0; i < sortedDirectionIndices.length; ++i) {
                    sortedDirectionIndices[i] = i;
                }                
            }
        }

        ThreadLocal<ThreadState> m_threadState = ThreadLocal.withInitial(() -> new ThreadState(this));

        public GeneticAlgorithm(long seed, int[] layerWidths) {
            m_random = new Random(seed);
            m_network = new Network(Game.kBoardSize, layerWidths, m_random);            
        }

        public static void SortIndices(double[] values, int[] sortedIndices) {
            for(int i = 0; i < values.length; ++i) {

                // place at end and bubble up to sorted position
                double result = values[i];
                sortedIndices[i] = i;
                
                for(int j = i-1; j >= 0; --j) {
                    int jResultIndex = sortedIndices[j];    

                    if(values[jResultIndex] >= result) break;

                    sortedIndices[j+1] = jResultIndex;
                    sortedIndices[j] = i;
                }
            }
        }

        public static int GetHighestBit(int value) {
            int bits = 0;
            while(value > (1 << bits)) {
                ++bits;
            }

            return bits;
        }

        public static double GetFitness(Game game) {

            // return .6 * game.m_maxTile + .3 * game.m_score + .1 *game.m_numMoves;
            return .6 * game.m_score + .3 * game.m_maxTile + .1 *game.m_numMoves;

            // return game.m_maxTile + game.m_score + game.m_numMoves;
            // return game.m_score;


            // double fitness = 0;
            // // double fitness = game.m_maxTile;
            // // double fitness = game.m_score;
            // // double fitness = game.m_score + game.m_numMoves;
            // // double fitness = game.m_maxTile + game.m_score + game.m_numMoves;

            // for(int y1 = 0; y1 < Game.kBoardHeight; ++y1) {
            //     for(int x1 = 0; x1 < Game.kBoardWidth; ++x1) {
                    
            //         int tile1 = game.GetTile(x1, y1);
            //         int tile1Bits = GetHighestBit(tile1);

            //         double tileFitness = Game.kBoardSize * tile1;
            //         for(int y2 = 0; y2 < Game.kBoardHeight; ++y2) {
            //             int absDY = (y2 > y1) ? (y2 - y1) : (y1 - y2);
                        
            //             for(int x2 = 0; x2 < Game.kBoardWidth; ++x2) {

            //                 // skip over ourselves
            //                 if(y1 == y2 && x1 == x2) continue;

            //                 int tile2 = game.GetTile(x2, y2);
            //                 int tile2Bits = GetHighestBit(tile2);

            //                 int absDX = (x2 > x1) ? (x2 - x1) : (x1 - x2);
            //                 int tileDistance = absDX + absDY;

            //                 int bitDistance = (tile2Bits > tile1Bits) ? (tile2Bits - tile1Bits) : (tile1Bits - tile2Bits);
                            
            //                 int absDT = (tile2 > tile1) ? (tile2 - tile1) : (tile1 - tile2);

            //                 final int kMaxTileDistance = Game.kBoardHeight + Game.kBoardWidth;
            //                 // final int kMaxBitDistance = 15;
                            
            //                 double penalty = (double)(absDT * (1 << tileDistance)) / ((1 << bitDistance) * (1 << kMaxTileDistance));

            //                 tileFitness-= penalty;
            //             }
            //         }

            //         fitness+= tileFitness;
            //     }
            // }

            // return fitness;
        }
 
        // Plays the game to completion using the the neural network and returns the final resulting game's fitness
        public double PlayGame(Game game, int msDelay) {
            
            ThreadState threadState                = m_threadState.get();
            int[] sortedDirectionIndices           = threadState.sortedDirectionIndices;
            Network.ThreadState networkThreadState = threadState.networkThreadState;

            while(!game.IsGameOver()) {

                // set board inputs
                for(int i = 0; i < networkThreadState.input.length; ++i) {
                    int tile = game.m_board[i];

                    // TODO: this is slow - what if we stored the board tileBits as double
                    //       and then just pulled the mantissa out of it? 

                    // Normalized input for the largest possible tile value of 131,072 = 2^17
                    int tileBits = GetHighestBit(tile);
                    networkThreadState.input[i] = tileBits * (1/17.0);
                }

                // TODO: Do we need to use EvalThreadSafe anymore or can we switch to standard Eval? 
                //       with the new way we train the Populations we only ever evaluate a
                //       network on a single thread at a time so we could use slightly faster m_network.Eval
                //       and move input array into threadState.
                //       Either way most of the time is spent playing the game
                //       not evaluating the network so this isn't really much of a bottle neck
                //       and removing this seems like it can cause heisenbugs later on down the road
                //       so lets just wait until it actually becomes a bottleneck  
                // double[] results = m_network.Eval(networkThreadState.input);                
                                
                // evaluate network
                double[] results = m_network.EvalThreadSafe(networkThreadState);


                // Note: this insertion sort is extremely fast and guarantees determinism with the same 
                //       game played on the same network (directionIndices.length = 4)
                SortIndices(results, sortedDirectionIndices);
                
                // make best move
                // Note: loop likely exits on first iteration
                for(int i = 0; i < sortedDirectionIndices.length; ++i) {
                    int directionIndex = sortedDirectionIndices[i];

                    if(game.Move(kDirections[directionIndex])) {
                        break;
                    }
                }

                if(msDelay > 0) {
                    try {
                        Thread.sleep(msDelay);
                    } catch (InterruptedException e) {}
                }
            }

            return GetFitness(game);
        }

        public void Reset() {
            m_network.Reset(m_random);
        }

        
        public double MutateWeight(double weight, double mutationRange) {
            return weight + weight * (2*mutationRange * m_random.nextDouble() - mutationRange);
        }
        
        public void Mutate(double mutationProbability, double mutationRange) {

            for(Layer layer : m_network.m_layers) {

                for(Neuron neuron : layer.m_neurons) {

                    for(int i = 0; i < neuron.m_weights.length; ++i) {
                        if(m_random.nextDouble() < mutationProbability) {
                            neuron.m_weights[i] = MutateWeight(neuron.m_weights[i], mutationRange);
                        }
                    }
                }
            }
        }

        public void MakeChild(GeneticAlgorithm p1, GeneticAlgorithm p2, double mutationProbability, double mutationRange) {

            for(int l = 0; l < m_network.m_layers.length; ++l) {
                Layer layer   = m_network.m_layers[l];
                Layer p1Layer = p1.m_network.m_layers[l];
                Layer p2Layer = p2.m_network.m_layers[l];

                for(int n = 0; n < layer.m_neurons.length; ++n) {
                    Neuron neuron   = layer.m_neurons[n];
                    Neuron p1Neuron = p1Layer.m_neurons[n];
                    Neuron p2Neuron = p2Layer.m_neurons[n];
                    
                    for(int w = 0; w < neuron.m_weights.length; ++w) {

                        // coin flip for parent neuron to inherit from
                        Neuron inheritedNeuron = m_random.nextBoolean() ? p1Neuron : p2Neuron;
                        double inheritedWeight = inheritedNeuron.m_weights[w];
                        
                        neuron.m_weights[w] = (m_random.nextDouble() < mutationProbability) ? MutateWeight(inheritedWeight, mutationRange) : inheritedWeight;
                    }
                }
            }
        }
    }

    public static class GameStats {
        int m_gameScore   = 0;
        int m_gameMoves   = 0;
        int m_gameMaxTile = 0;
        double m_fitness  = 0;

        public void Set(int value) {
            m_gameScore   = value;
            m_gameMoves   = value;
            m_gameMaxTile = value;
            m_fitness     = value;
        }

        public void Set(GameStats stats) {
            m_gameScore   = stats.m_gameScore;
            m_gameMoves   = stats.m_gameMoves;
            m_gameMaxTile = stats.m_gameMaxTile;
            m_fitness     = stats.m_fitness;
        }

        public void Add(GameStats stats) {
            m_gameScore   += stats.m_gameScore;
            m_gameMoves   += stats.m_gameMoves;
            m_gameMaxTile += stats.m_gameMaxTile;
            m_fitness     += stats.m_fitness;
        }

        public void Max(GameStats stats) {
            if(m_gameScore   < stats.m_gameScore  ) m_gameScore   = stats.m_gameScore;
            if(m_gameMoves   < stats.m_gameMoves  ) m_gameMoves   = stats.m_gameMoves;
            if(m_gameMaxTile < stats.m_gameMaxTile) m_gameMaxTile = stats.m_gameMaxTile;
            if(m_fitness     < stats.m_fitness    ) m_fitness     = stats.m_fitness;
        }

        public void Min(GameStats stats) {
            if(m_gameScore   > stats.m_gameScore  ) m_gameScore   = stats.m_gameScore;
            if(m_gameMoves   > stats.m_gameMoves  ) m_gameMoves   = stats.m_gameMoves;
            if(m_gameMaxTile > stats.m_gameMaxTile) m_gameMaxTile = stats.m_gameMaxTile;
            if(m_fitness     > stats.m_fitness    ) m_fitness     = stats.m_fitness;
        }

        // TODO: Clean this up if possible without incurring cost of constructing GameStat in inner train loops 
        public void Add(Game game, double fitness) {
            m_gameScore   += game.m_score;
            m_gameMoves   += game.m_numMoves;
            m_gameMaxTile += game.m_maxTile;
            m_fitness     += fitness;
        }

        public void Max(Game game, double fitness) {
            if(m_gameScore   < game.m_score   ) m_gameScore   = game.m_score;
            if(m_gameMoves   < game.m_numMoves) m_gameMoves   = game.m_numMoves;
            if(m_gameMaxTile < game.m_maxTile ) m_gameMaxTile = game.m_maxTile;
            if(m_fitness     < fitness        ) m_fitness     = fitness;
        }

        public void Min(Game game, double fitness) {
            if(m_gameScore   > game.m_score   ) m_gameScore   = game.m_score;
            if(m_gameMoves   > game.m_numMoves) m_gameMoves   = game.m_numMoves;
            if(m_gameMaxTile > game.m_maxTile ) m_gameMaxTile = game.m_maxTile;
            if(m_fitness     > fitness        ) m_fitness     = fitness;
        }
    }

    public static class GameWorkerResult {
        GameStats min   = new GameStats();
        GameStats max   = new GameStats();
        GameStats total = new GameStats();

        public GameWorkerResult() {
            Clear();
        }

        public void Clear() {
            min.Set(Integer.MAX_VALUE);
            max.Set(0);
            total.Set(0);
        }

        public void Set(GameWorkerResult result) {
            min.Set(result.min);
            max.Set(result.max);
            total.Set(result.total);
        }

        public void Add(Game game, double fitness) {
            min.Min(game, fitness);
            max.Max(game, fitness);
            total.Add(game, fitness);
        }

        public void Add(GameWorkerResult result) {
            min.Min(result.min);
            max.Max(result.max);
            total.Add(result.total);
        }
    }

    public static abstract class GameWorker implements Callable<Object>, Comparable<GameWorker> {
        int m_id;
        GameWorkerResult m_result = new GameWorkerResult();

        public GameWorker(int id) {            
            m_id = id;
        }
    
        @Override
        public int compareTo(GameWorker worker) {
            GameWorkerResult results1 = m_result;
            GameWorkerResult results2 = worker.m_result;
            
            double value1 = results1.total.m_fitness;
            double value2 = results2.total.m_fitness;

            // TODO: should we use total min/max tile for better ordering?
            if(value1 == value2) {
                value1 = results1.min.m_fitness;
                value2 = results2.min.m_fitness;                    
            }

            if(value1 == value2) {
                value1 = results1.max.m_fitness;
                value2 = results2.max.m_fitness;                    
            }

            return (value1 > value2) ? -1 :
                    (value1 < value2) ?  1 : 0;
        }

        public Object PlayGame(long gameSeed, GeneticAlgorithm algorithm) {
            Game game = new Game(gameSeed);            
            double fitness = algorithm.PlayGame(game, 0);
            
            m_result.Add(game, fitness);
            return null;
        }

        public static <T extends GameWorker> void Invoke(ExecutorService threadPool, ArrayList<T> gameWorkers) {
            try {
                threadPool.invokeAll(gameWorkers);
            } catch (InterruptedException e) {
                e.printStackTrace();
                System.exit(1);
            }            
        }

        public static <T extends GameWorker> void ClearResults(ArrayList<T> gameWorkers) {
            for(GameWorker worker : gameWorkers) {
                worker.m_result.Clear();
            }     
        }
        
        public static <T extends GameWorker> GameWorkerResult GetCumulativeResult(ArrayList<T> gameWorkers) {
            
            // TODO: move this to GameWorkerResult
            GameWorkerResult cumulative = new GameWorkerResult();
            for(GameWorker gameWorker : gameWorkers) {
                cumulative.Add(gameWorker.m_result);
            }

            return cumulative;

        }
    }
    
    public static class Pointer<T> {
        public T value;
    }
    
    // Note: can't instantiate generic primitives and we don't want the overhead of 'Long' 
    public static class LongPtr {
        public long value;        
    }

    public static class DemographicGameWorker extends GameWorker {
        Demographic m_demographic;
        GeneticAlgorithm m_algorithm;

        // TODO: should these be tracked inside GeneticAlgorithm?
        long m_algorithmId   = 0;
        boolean m_invincible = false;

        long m_resultBatchId     = 0;
        long m_resultAlgorithmId = 0;
     
        public DemographicGameWorker(int id, GeneticAlgorithm algorithm, Demographic demographic) {
            super(id);
            m_demographic = demographic;
            m_algorithm   = algorithm;
        }

        @Override
        public Object call() {
            boolean updateNeeded = m_demographic.m_workerForceUpdate || 
                                  (m_resultBatchId     != m_demographic.m_currentBatchId) ||
                                  (m_resultAlgorithmId != m_algorithmId);

            if(Demographic.m_kDebugWorkers) {
                System.out.println(
                    "Batch: " + m_demographic.m_currentBatchId +
                    " - [Update: " + updateNeeded + 
                    " | force: " + m_demographic.m_workerForceUpdate +
                    "] | gameSeed: " + m_demographic.m_workerTrainingSeed +
                    " | Alg: " + m_id +
                    " | currentBatchId: " + m_demographic.m_currentBatchId +
                    " | algorithmId: " + m_algorithmId +
                    " | updateResultIds: " + m_demographic.m_workerUpdateResultIds +
                    " | resultBatchId: " + m_resultBatchId +
                    " | resultAlgorithmId: "+ m_resultAlgorithmId
                );
            }

            if(!updateNeeded) return null;

            if(m_demographic.m_workerClearResults) {
                m_result.Clear();
            }

            PlayGame(m_demographic.m_workerTrainingSeed, m_algorithm);

            if(m_demographic.m_workerUpdateResultIds) {
                m_resultBatchId     = m_demographic.m_currentBatchId;
                m_resultAlgorithmId = m_algorithmId;
            }
            
            return null;
        }
    }

    public static class DemographicParameters {
        int numAlgorithms;
        int[] layerWidths;
        
        int trainingSetSize;

        ExecutorService threadPool;
    }

    public static class DemographicTrainingParameters {
        int batchSize;

        int mutationCount;
        int survivalCount;
        int extinctionSurvivalCount;

        int luckyPoolSize;
        double luckyRate;
        double luckyMutationRate;
        double luckyMutationRange;
        
        double extinctionRate;
    
        double mutationRate;
        double mutationRange;
        
        int    crossoverPoolSize;        
        double crossoverMutationRate;
        double crossoverMutationRange;
    }

    public static class Demographic {
        static final boolean m_kDebugWorkers = false;

        Random m_random;
        DemographicParameters m_parameters;

        GeneticAlgorithm[] m_algorithms;
        Integer[] m_algorithmIndices;

        long[] m_trainingSeeds;
        int[] m_batchTrainingIndices;
        
        long m_currentBatchId; // monotonically increasing for each batch created
        int m_currentBatchSize;
        int m_currentBatchStartIndex;

        ArrayList<DemographicGameWorker> m_gameWorkers;
        boolean m_isGameWorkersSorted = false;

        long m_workerTrainingSeed;
        boolean m_workerForceUpdate     = false;
        boolean m_workerClearResults    = false;
        boolean m_workerUpdateResultIds = false;

        public Demographic(long seed, DemographicParameters params) {
            m_random     = new Random(seed);
            m_parameters = params;

            // create training data
            m_trainingSeeds = new long[params.trainingSetSize];
            m_batchTrainingIndices = new int[params.trainingSetSize];

            for(int i = 0; i < params.trainingSetSize; ++i) {
                m_trainingSeeds[i] = m_random.nextLong();
                m_batchTrainingIndices[i] = i;
            }

            // create algorithms
            m_algorithms       = new GeneticAlgorithm[params.numAlgorithms];
            m_algorithmIndices = new Integer[params.numAlgorithms];
            m_gameWorkers      = new ArrayList<>(params.numAlgorithms);

            for(int i = 0; i < params.numAlgorithms; ++i) {

                long algorithmSeed = m_random.nextLong();
                GeneticAlgorithm algorithm = new GeneticAlgorithm(algorithmSeed, params.layerWidths);
                
                m_algorithms[i] = algorithm;
                m_algorithmIndices[i] = i;
                
                m_gameWorkers.add(new DemographicGameWorker(i, algorithm, this));
            }
        }

        public void SortGameWorkers() {
            // Lazy sorting to speed up training in inner loops
            if(!m_isGameWorkersSorted) {
                Collections.sort(m_gameWorkers);
                m_isGameWorkersSorted = true;
            }
        }

        public DemographicGameWorker GetBestGameWorker() {
            
            // reevaluate dirty algorithms in current batch
            InvokeBatch(m_parameters.threadPool, m_currentBatchStartIndex, m_currentBatchSize, m_trainingSeeds, false);

            int remainingBatchSize = m_batchTrainingIndices.length - m_currentBatchSize;
            if(remainingBatchSize > 0) {
                // configure new batch to be all training data
                // Note: we do this before MergeBatch so gameWorker.m_resultLastBatchId updates to it
                //       and subsequent calls to GetBestGameWorker and InvokeBatch don't cause a recompute  
                ++m_currentBatchId;
                m_currentBatchStartIndex = 0;
                m_currentBatchSize = m_batchTrainingIndices.length;

                // merge remaining training data results into the new batch
                InvokeBatch(m_parameters.threadPool, 0, remainingBatchSize, m_trainingSeeds, true);
            }

            // get best worker
            SortGameWorkers();
            return m_gameWorkers.get(0);
        }

        protected void CreateRandomBatch(int batchSize) {
            // Computes a random batch of 'batchSize' training from m_batchTrainingIndices
            // the random indices are placed at the end of the m_batchTrainingIndices array
            // Returns the first index of batch in m_batchTrainingIndices 
            // Requires 'batchSize' in range [0, m_batchTrainingIndices.length]

            ++m_currentBatchId;
            m_currentBatchSize = batchSize;
            m_currentBatchStartIndex = m_batchTrainingIndices.length - batchSize;

            for(int i = 0; i < batchSize; ++i) {
                // sample random trainingIndex without replacement
                int sampleSize          = m_batchTrainingIndices.length - i;
                int sampleIndex         = m_random.nextInt(sampleSize);
                int sampleTrainingIndex = m_batchTrainingIndices[sampleIndex];
                
                // swap random sample at the tail of the array
                int tailSampleIndex   = sampleSize - 1;
                int tailTrainingIndex = m_batchTrainingIndices[tailSampleIndex];
                
                m_batchTrainingIndices[sampleIndex]     = tailTrainingIndex;
                m_batchTrainingIndices[tailSampleIndex] = sampleTrainingIndex;
            }
        }

        public void InvokeBatch(ExecutorService threadPool, int batchStartIndex, int batchSize, long[] gameSeeds, boolean appendResults) {
            if(batchSize <= 0) return;

            // TODO: Right now this marks the data as unsorted
            //       optimize this to only mark data as unsorted if there exists a dirty gameWorker algorithm
            //       that will be updated. AKA optimize the path: TrainAllTrainingData(batch 1) -> GetBestWorker(sorts) -> TrainAllTrainingData(batch1, but will resort sorted data)
            //       we can do this by just tracking a has dirty flag in demographic that gets set by Train (AND POPULATION- might want a setter) and then 
            //       gets cleared at InvokeBatch if a parameter is passed through?
            m_isGameWorkersSorted = false;

            m_workerForceUpdate = appendResults;
            m_workerClearResults = !appendResults;

            int lastI = batchSize - 1;
            for(int i = 0; i < batchSize; ++i) {

                // Evaluate all algorithms with same game batch seed
                int trainingIndex       = m_batchTrainingIndices[batchStartIndex + i];
                m_workerTrainingSeed    = gameSeeds[trainingIndex];                
                m_workerUpdateResultIds = (i == lastI);

                GameWorker.Invoke(threadPool, m_gameWorkers);
            
                // append remaining of batch results
                m_workerClearResults = false;
            }
        }

        public void Train(DemographicTrainingParameters trainParams) {
            
            int maxBatchSize = m_batchTrainingIndices.length;
            int batchSize = Math.min(maxBatchSize, trainParams.batchSize);

            boolean reuseLastBatch = (batchSize == maxBatchSize) && (m_currentBatchSize == maxBatchSize);
            if(!reuseLastBatch) {
                CreateRandomBatch(batchSize);
            }

            // evaluate all the algorithms on the current batch 
            InvokeBatch(m_parameters.threadPool, m_currentBatchStartIndex, batchSize, m_trainingSeeds, false);
            
            // sort m_gameWorkers to partition them into surviving / crossover / mutation groups
            SortGameWorkers();
            
            // evolve algorithms 
            boolean isExtinction = (m_random.nextDouble() < trainParams.extinctionRate);
            if(isExtinction) {

                // replace all nonsurviviors with new networks
                for(int i = trainParams.extinctionSurvivalCount; i < m_parameters.numAlgorithms; ++i) {
                    DemographicGameWorker worker = m_gameWorkers.get(i);
                    
                    // ignore invincible workers
                    if(worker.m_invincible) continue;

                    ++worker.m_algorithmId;
                    worker.m_algorithm.Reset();
                }
            
            } else {
                // Normal training
                int crossoverIndex = trainParams.survivalCount + trainParams.mutationCount;

                // Update all non surviving algorithms
                // Note: we traverse backwards to allow crossover to complete prior to mutations
                for(int i = m_parameters.numAlgorithms - 1; i >= trainParams.survivalCount; --i) {              
                    DemographicGameWorker worker = m_gameWorkers.get(i);

                    // ignore invincible workers
                    if(worker.m_invincible) continue;

                    ++worker.m_algorithmId;
                    GeneticAlgorithm algorithm = worker.m_algorithm;
                    
                    boolean isLucky = m_random.nextDouble() < trainParams.luckyRate;
                    if(isLucky) {

                        // congrats! make a child with the top lucky pool
                        int parent2Index = m_random.nextInt(trainParams.luckyPoolSize);
                        DemographicGameWorker parent2 = m_gameWorkers.get(parent2Index);

                        algorithm.MakeChild(algorithm, parent2.m_algorithm, trainParams.luckyMutationRate, trainParams.luckyMutationRange);

                    } else if(i < crossoverIndex) {

                        // mutate top performing algorithms 
                        algorithm.Mutate(trainParams.mutationRate, trainParams.mutationRange);

                    } else {
                        // replace remaining low performing algorithms with children of best algorithms
                        // Note: we allow parent1 == parent2 to increases diversity with mutations of survivors.

                        int parent1Index = m_random.nextInt(trainParams.crossoverPoolSize);
                        int parent2Index = m_random.nextInt(trainParams.crossoverPoolSize);

                        DemographicGameWorker parent1 = m_gameWorkers.get(parent1Index);
                        DemographicGameWorker parent2 = m_gameWorkers.get(parent2Index);

                        algorithm.MakeChild(parent1.m_algorithm, parent2.m_algorithm, trainParams.crossoverMutationRate, trainParams.crossoverMutationRange);
                    }
                }
            }

            m_isGameWorkersSorted = false;
        }
    }

    public static class PopulationParameters {
        int numDemographics;

        NetworkGUI networkGUI = null;
        int numPopulationGraphPoints = -1;
        int numDemographicGraphPoints = -1;

        DemographicParameters demographicParameters;
        ExecutorService threadPool;
    }

    public static class PopulationTrainingParameters {
        DemographicTrainingParameters demographicTrainingParameters;
        
        int trainingsPerDemographic;

        int migrationCount;
        int migrationResistantCount;

        int    crossbreedCount;
        int    crossbreedPoolSize;
        double crossbreedMutationRate;
        double crossbreedMutationRange;
    }

    public static class PopulationGameWorker extends GameWorker {
        DemographicGameWorker m_demographicGameWorker;
        Population m_population;

        long m_resultAlgorithmId = 0;

        public PopulationGameWorker(int id, Population population, DemographicGameWorker demographicGameWorker) {
            super(id);

            m_population = population;
            m_demographicGameWorker = demographicGameWorker;
        }

        @Override
        public Object call() {

            // algorithm hasn't changed reuse cached result (training data is constant)
            if(m_resultAlgorithmId == m_demographicGameWorker.m_resultAlgorithmId) return null;

            if(m_population.m_workerCopyDemographicResults) {

                // copy over the solution for all of our training / initial results
                m_result.Set(m_demographicGameWorker.m_result);
                return null;
            }

            // add our game results update the cached result
            PlayGame(m_population.m_workerGameSeed, m_demographicGameWorker.m_algorithm);
             
            if(m_population.m_workerUpdateResultIds) {
                m_resultAlgorithmId = m_demographicGameWorker.m_resultAlgorithmId;
             }

            return null;
        }
    }

    public static class Population {
        Random m_random;
        PopulationParameters m_parameters;
        int m_trainingSetSize;

        Demographic[] m_demographics;

        ArrayList<PopulationGameWorker>[] m_gameWorkerArrays;
        boolean m_workerCopyDemographicResults;
        boolean m_workerUpdateResultIds;
        long m_workerGameSeed;

        // TODO: replace this with a sorted array of all gameWorkers that we maintain
        //       that way we can just pull the top n to set invincibility. 
        //       can we also use a gameWorker flag to clear invincibility too? 
        DemographicGameWorker m_invincibleGameWorker = null;

        // Note: 1 network and graph panel for each demographic and +1 for validation
        GraphPanel[] m_graphPanels;
        NetworkPanel[] m_networkPanels;

        public Color m_backgroundDemographicColor = Color.gray;
        public Color m_foregroundDemographicColor = Color.lightGray;

        public Color m_backgroundPopulationColor  = new Color(0, 128, 128); //dark cyan
        public Color m_foregroundPopulationColor   = new Color(0, 255, 255); //light cyan

        public Population(long randomSeed, PopulationParameters params) {
            m_random           = new Random(randomSeed);
            m_parameters       = params;
            m_trainingSetSize  = params.numDemographics * params.demographicParameters.trainingSetSize;
            m_demographics     = new Demographic[params.numDemographics];
            m_gameWorkerArrays = new ArrayList[params.numDemographics];

            // +1 for cumulative population stats
            int numGUIItems = params.numDemographics + 1;
            m_graphPanels      = new GraphPanel[numGUIItems];
            m_networkPanels    = new NetworkPanel[numGUIItems];

            String[] inputNames = new String[Game.kBoardSize];
            for(int y = 0; y < Game.kBoardHeight; ++y) {
                for(int x = 0; x < Game.kBoardWidth; ++x) {
                    inputNames[y*Game.kBoardWidth + x] = x+","+y;
                }
            }
            
            final int kNumDirections = GeneticAlgorithm.kDirections.length;
            String[] outputNames = new String[kNumDirections];
            Color[] outputColors = new Color[kNumDirections];
            for(int i = 0; i < kNumDirections; ++i) {
                outputNames[i] = GeneticAlgorithm.kDirections[i].name();
                
                float colorHue = i/(float)kNumDirections;
                outputColors[i] = Color.getHSBColor(colorHue, 1, 1);
            }
            
            // create Demographics and GUI items
            int gameWorkerId = 0;
            for(int i = 0; i < numGUIItems; ++i) {
                
                String guiItemName;
                Color guiItemColor;
                int numGraphPoints;

                int demographicTrainingSetSize = params.demographicParameters.trainingSetSize;

                if(i < params.numDemographics) {

                    // create demographic
                    long demographicSeed = m_random.nextLong();
                    Demographic demographic = new Demographic(demographicSeed, params.demographicParameters);
                    m_demographics[i] = demographic;
                    
                    // create game workers for demographic
                    ArrayList<PopulationGameWorker> gameWorkers = new ArrayList<>(demographicTrainingSetSize);
                    for(DemographicGameWorker demographicGameWorker : demographic.m_gameWorkers) {
                        gameWorkers.add(new PopulationGameWorker(gameWorkerId++, this, demographicGameWorker));
                    }
                    m_gameWorkerArrays[i] = gameWorkers;

                    guiItemName    = getDemographicGuiStr(i, -1);
                    guiItemColor   = m_backgroundDemographicColor;
                    numGraphPoints = params.numDemographicGraphPoints;
                    
                } else {
                    guiItemName    = getPopulationGuiStr(-1, -1);
                    guiItemColor   = m_backgroundPopulationColor;
                    numGraphPoints = params.numPopulationGraphPoints;
                }

                // create networkPanel
                NetworkGUI networkGUI = params.networkGUI;
                NetworkPanel networkPanel = networkGUI.AddNetworkPanel(guiItemName, null, inputNames, outputNames, outputColors);
                networkPanel.m_nameColor = guiItemColor;
                m_networkPanels[i] = networkPanel;

                // create graph
                if(numGraphPoints > 0) {
                    double[] graphData = new double[numGraphPoints];

                    GraphPanel graph = networkGUI.AddGraph(guiItemName, numGraphPoints, graphData, 0, 0);

                    graph.m_xMin = 0;
                    graph.m_xMax = numGraphPoints;
                    
                    // Note: initialized reversed so graph scales on first update no mater fitness
                    graph.m_yMin = Double.MAX_VALUE;
                    graph.m_yMax = Double.MIN_VALUE;

                    graph.m_mode  = GraphMode.SCROLL;
                    graph.m_color = guiItemColor;

                    m_graphPanels[i] = graph;
                }
            }
        }

        // TODO: Should this return PopulationGameWorker? or should we just Train
        //       in tight loop and query have a separate GetBestGameWorker similar to demographic? 
        public PopulationGameWorker Train(PopulationTrainingParameters trainParams) {

            // Unhighlight population graph 
            NetworkPanel populationNetworkPanel = m_networkPanels[m_parameters.numDemographics];
            GraphPanel   populationGraphPanel   = m_graphPanels[m_parameters.numDemographics];

            populationGraphPanel.m_color       = m_backgroundPopulationColor;
            populationNetworkPanel.m_nameColor = m_backgroundPopulationColor;

            // train each demographic
            for(int i = 0; i < m_parameters.numDemographics; ++i) {
                
                // TODO: Pack this into class to make things cleaner
                //       we could also move the plotting logic there?
                Demographic demographic   = m_demographics[i];
                GraphPanel graphPanel     = m_graphPanels[i];
                NetworkPanel networkPanel = m_networkPanels[i];

                graphPanel.m_color = m_foregroundDemographicColor;
                networkPanel.m_nameColor = m_foregroundDemographicColor;

                for(int t = 0; t < trainParams.trainingsPerDemographic; ++t) {
                
                    demographic.Train(trainParams.demographicTrainingParameters);
                    
                    DemographicGameWorker bestWorker = demographic.GetBestGameWorker();
                    GeneticAlgorithm bestAlgorithm   = bestWorker.m_algorithm;
                    
                    String demographicGuiStr = getDemographicGuiStr(i, bestWorker.m_id);
                    
                    // TODO: Do we need to copy weights for multithreading?
                    networkPanel.m_network = bestAlgorithm.m_network;
                    networkPanel.m_name = demographicGuiStr;

                    double avgTrainingSetFitness = bestWorker.m_result.total.m_fitness / m_parameters.demographicParameters.trainingSetSize;
                    graphPanel.pushPoint(avgTrainingSetFitness, true);
                    graphPanel.m_name = demographicGuiStr;

                    // TODO: Plot min & max on same graph too!

                    // TODO: HEREERERER!!!
                    //       plot min / max / avg diversity of the survivors as well to see how things progress over time
                    //       where diversity is the distance to the mean network... this could also create a good policy for
                    //       sorting / breaking ties in a demographic! Choosing the best performing network that is also the most
                    //       diverse will help prevent get stuck in local minima especially when games get further along and we need
                    //       to make 'large' changes to get to the next increase in fitness! 
                }

                graphPanel.m_color = m_backgroundDemographicColor;
                networkPanel.m_nameColor = m_backgroundDemographicColor;
            }

            // TODO: prevent crossbreeding in same demographic and also prevent multiple replacement of same child!
            // crossbred
            for(int i = 0; i < m_parameters.numDemographics; ++i) {
                Demographic demographic1 = m_demographics[i];
                
                for(int j = 0; j < trainParams.crossbreedCount; ++j) {

                    int demographic2Index = m_random.nextInt(m_parameters.numDemographics);
                    Demographic demographic2 = m_demographics[demographic2Index];
                    
                    // select worst performer as a child
                    int childIndex = demographic1.m_parameters.numAlgorithms - i - 1;
                    DemographicGameWorker childWorker = demographic2.m_gameWorkers.get(childIndex);

                    // don't modify invincible children
                    // TODO: this should keep searching for the first non invincible one
                    if(childWorker.m_invincible) continue;

                    // sample best performers for parents
                    int parentIndex1 = m_random.nextInt(trainParams.crossbreedPoolSize);
                    int parentIndex2 = m_random.nextInt(trainParams.crossbreedPoolSize);

                    DemographicGameWorker parentWorker1 = demographic1.m_gameWorkers.get(parentIndex1);
                    DemographicGameWorker parentWorker2 = demographic2.m_gameWorkers.get(parentIndex2);

                    // mingle
                    GeneticAlgorithm parent1 = parentWorker1.m_algorithm; 
                    GeneticAlgorithm parent2 = parentWorker2.m_algorithm; 
                    GeneticAlgorithm child   = childWorker.m_algorithm; 

                    child.MakeChild(parent1, parent2, trainParams.crossbreedMutationRate, trainParams.crossbreedMutationRange);
                    ++childWorker.m_algorithmId;
                }            
            }

            // perform migrations
            int migrationPoolSize = trainParams.migrationCount - trainParams.migrationResistantCount;
            for(int i = 0; i < m_parameters.numDemographics; ++i) {
                Demographic demographic1 = m_demographics[i];
                
                for(int j = 0; j < trainParams.migrationCount; ++j) {

                    int demographic2Index = m_random.nextInt(m_parameters.numDemographics);
                    Demographic demographic2 = m_demographics[demographic2Index];
                    
                    // select migrants from non migration resistant top performers
                    int migrationIndex1 = m_random.nextInt(migrationPoolSize) + trainParams.migrationResistantCount;
                    int migrationIndex2 = m_random.nextInt(migrationPoolSize) + trainParams.migrationResistantCount;

                    // migrate
                    DemographicGameWorker worker1 = demographic1.m_gameWorkers.get(migrationIndex1);
                    DemographicGameWorker worker2 = demographic2.m_gameWorkers.get(migrationIndex2);

                    GeneticAlgorithm algorithm1 = worker1.m_algorithm; 
                    GeneticAlgorithm algorithm2 = worker2.m_algorithm; 

                    boolean invincible1 = worker1.m_invincible;
                    boolean invincible2 = worker2.m_invincible;

                    // swap algorithms
                    worker1.m_algorithm = algorithm2;
                    worker2.m_algorithm = algorithm1;

                    ++worker1.m_algorithmId;
                    ++worker2.m_algorithmId;

                    // swap invincibility
                    worker1.m_invincible = invincible2;
                    worker2.m_invincible = invincible1;

                    if(m_invincibleGameWorker == worker1) {
                        m_invincibleGameWorker = worker2;
                    } else if(m_invincibleGameWorker == worker2) {
                        m_invincibleGameWorker = worker1;
                    }
                }    
            }
            
            // highlight population graph
            populationGraphPanel.m_color       = m_foregroundPopulationColor;
            populationNetworkPanel.m_nameColor = m_foregroundPopulationColor;

            // Get the best game worker for the entire population
            PopulationGameWorker bestGameWorker = GetBestGameWorker();

            int algorithmsPerDemographic = m_parameters.demographicParameters.numAlgorithms;
            int bestGameWorkerDemographicIndex = bestGameWorker.m_id / algorithmsPerDemographic;
            int bestGameWorkerAlgorithmIndex   = bestGameWorker.m_id % algorithmsPerDemographic;

            // Note: asserts assert's aren't always enabled ...this is
            if(bestGameWorkerAlgorithmIndex != bestGameWorker.m_demographicGameWorker.m_id) {
                System.out.println("INCORRECTLY MAPPED ALGORITHM INDEX!");
            }

            String populationGuiStr = getPopulationGuiStr(bestGameWorkerDemographicIndex, bestGameWorkerAlgorithmIndex);
            double bestResultAvgFitness = bestGameWorker.m_result.total.m_fitness / m_trainingSetSize;

            populationNetworkPanel.m_network = bestGameWorker.m_demographicGameWorker.m_algorithm.m_network;
            populationNetworkPanel.m_name = populationGuiStr;

            populationGraphPanel.pushPoint(bestResultAvgFitness, true);    
            populationGraphPanel.m_name = populationGuiStr;

            // TODO: replace this with a tunable parameter / count
            if(m_invincibleGameWorker != null) {
                m_invincibleGameWorker.m_invincible = false;
            }
            m_invincibleGameWorker = bestGameWorker.m_demographicGameWorker;
            m_invincibleGameWorker.m_invincible = true;

            // TODO: THIS IS A HACK! - move this logic into Demographic once we get
            //       logic tested and working well
            // crossbreed the worst demographic workers with the invincible ones 
            for(Demographic demographic : m_demographics) {

                // sort gameWorkers
                demographic.GetBestGameWorker();
                
                int numGameWorkers = demographic.m_gameWorkers.size();
                for(int i = (int)(.95 * numGameWorkers); i < numGameWorkers; ++i) {
                    
                    DemographicGameWorker child = demographic.m_gameWorkers.get(i);
                    if(child.m_invincible) continue;
                    
                    int parent2Index = demographic.m_random.nextInt(numGameWorkers);
                    DemographicGameWorker parent2 = demographic.m_gameWorkers.get(parent2Index);
                
                    // TODO: we should really sample from a pool of invincible algorithms
                    child.m_algorithm.MakeChild(m_invincibleGameWorker.m_algorithm, parent2.m_algorithm, .1, 1);
                    ++child.m_algorithmId;
                }

                demographic.m_isGameWorkersSorted = false;
            }

            return bestGameWorker;
        }

        public PopulationGameWorker GetBestGameWorker() {
            PopulationGameWorker bestGameWorker = null;
                        
            for(int i = 0; i < m_parameters.numDemographics; ++i) {                
                ArrayList<PopulationGameWorker> iGameWorkers = m_gameWorkerArrays[i];

                // make sure all training data is evaluated for current gameWorker demographic 
                // TODO: optimize this with dirty flag in Demographic to prevent rescheduling all threads!
                Demographic demographic = m_demographics[i];
                demographic.GetBestGameWorker();

                // enable caching results on last GameWorker.Invoke
                m_workerUpdateResultIds = (m_parameters.numDemographics == 1);

                // Initialize iGameWorkers results from with demographic i's training data results
                m_workerCopyDemographicResults = true;
                GameWorker.Invoke(m_parameters.threadPool, iGameWorkers);
                m_workerCopyDemographicResults = false;

                // evaluate iGameWorkers on remaining demographic training data
                for(int j = 0; j < m_parameters.numDemographics; ++j) {
                    if(i == j) continue;

                    int lastInvokedJ = m_parameters.numDemographics - 1;
                    if(lastInvokedJ == i) --lastInvokedJ;

                    Demographic jDemographic = m_demographics[j]; 

                    int lastSeedIndex = jDemographic.m_trainingSeeds.length - 1;
                    for(int seedIndex = 0; seedIndex <= lastSeedIndex; ++seedIndex) {

                        // enable caching results on last GameWorker.Invoke
                        // TODO: is there a cleaner way to do this
                        //       this technically breaks / disables caching if lastDemographic doesn't have any training data
                        //       (which shouldn't happen, but still)
                        m_workerUpdateResultIds = ((j == lastInvokedJ) && (seedIndex == lastSeedIndex));

                        // if(m_workerUpdateResultBatchId) {
                        //     System.out.println("I - i:"+i+" | j:"+j+" | s:"+seedIndex);
                        // } else {
                        //     System.out.println("P - i:"+i+" | j:"+j+" | s:"+seedIndex);
                        // }

                        m_workerGameSeed = jDemographic.m_trainingSeeds[seedIndex];
                        GameWorker.Invoke(m_parameters.threadPool, iGameWorkers);
                    }
                                
                    m_workerUpdateResultIds = false;
                }

                // get the best result
                // TODO: should we just sort this so we can mark multiple invincible algorithms?
                for(PopulationGameWorker gameWorker : iGameWorkers) {
                    if(bestGameWorker == null || bestGameWorker.compareTo(gameWorker) > 0) {
                        bestGameWorker = gameWorker;
                    } 
                }
            }

            return bestGameWorker;
        }

        int numDigits(int i) {
            int result = 1;
            while((i/=10) > 0) {
                result+= 1;
            }
            return result;
        }

        String getAlgorithmStr(String prefix, int demographicId, int algorithmId) {
            // TODO: benchmark this -- if its too slow we should just cache the strings
            // Java string formatting / String builder look like trash

            int maxDemographicDigits = numDigits(m_parameters.numDemographics);
            int maxAlgorithmDigits   = numDigits(m_parameters.demographicParameters.numAlgorithms);

            StringBuilder result = new StringBuilder(prefix.length() + maxDemographicDigits + 1 + maxAlgorithmDigits);
            result.append(prefix);

            // append demographicId
            int numDemographicSpace = (demographicId < 0) ? (maxDemographicDigits - 1) : (maxDemographicDigits - numDigits(demographicId));
            for(int i = 0; i < numDemographicSpace; ++i) {
                result.append(' ');
            }
            if(demographicId < 0) {
                result.append('?');
            } else {
                result.append(demographicId);
            }

            // separator
            result.append(':');

            // append algorithmId 
            if(algorithmId < 0) {
                
                result.append('?');           
                int numAlgorithmSpace = maxAlgorithmDigits - 1;
                for(int i = 0; i < numAlgorithmSpace; ++i) {
                    result.append(' ');
                }

            } else {

                int numAlgorithmZero = maxAlgorithmDigits - numDigits(algorithmId);
                for(int i = 0; i < numAlgorithmZero; ++i) {
                    result.append('0');
                }
                result.append(algorithmId);
            }

            return result.toString();
        }

        String getDemographicGuiStr(int demographicId, int algorithmId) {
            return getAlgorithmStr("D ", demographicId, algorithmId);
        }

        String getPopulationGuiStr(int demographicId, int algorithmId) {
            return getAlgorithmStr("P ", demographicId, algorithmId);
        }   
    }

    public static class AIParameters {
        long seed = 42;
        int defaultNumThreads = 1;

        int defaultNumPopulationGraphPoints = 0;
        int defaultNumDemographicGraphPoints = 0;
        int validationSetSize = 10;
        
        PopulationParameters populationParameters;
    }

    public static class AITrainingParameters {
        int numEpochs;
        int outputStride;
       
        PopulationTrainingParameters populationTrainingParameters;
    }

    public static class AI {    
        Random m_random;
        Population m_population;
        
        AIParameters m_parameters;
        NetworkGUI m_networkGui;
        
        long[] m_validationGameSeeds;

        public AI(AIParameters params) {
            m_parameters = params;

            m_random = new Random(params.seed);

            PopulationParameters  populationParams  = params.populationParameters;
            DemographicParameters demographicParams = populationParams.demographicParameters;

            if(populationParams.threadPool == null || demographicParams.threadPool == null) {
                ExecutorService defaultThreadPool = Executors.newFixedThreadPool(params.defaultNumThreads);

                if(populationParams.threadPool == null) {
                   populationParams.threadPool = defaultThreadPool; 
                }

                if(demographicParams.threadPool == null) {
                   demographicParams.threadPool = defaultThreadPool; 
                }             
            }

            m_validationGameSeeds = new long[params.validationSetSize];
            for(int i = 0; i < params.validationSetSize; ++i) {
                m_validationGameSeeds[i] = m_random.nextLong();
            }

            m_networkGui = new NetworkGUI("2048 Genetic Algorithm");
            m_networkGui.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);

            // TODO: Add validation graph to network GUI

            if(populationParams.networkGUI == null) {
                populationParams.networkGUI = m_networkGui;
            }

            // TODO: this is wonky ... we want to specify the number of graph points
            //       in aiParameters, but create the graphs via populationParams ...
            //       we should create the gui in here and then pass it to the population?
            if(populationParams.numPopulationGraphPoints < 0) {
                populationParams.numPopulationGraphPoints = params.defaultNumPopulationGraphPoints;
            }

            if(populationParams.numDemographicGraphPoints < 0) {
                populationParams.numDemographicGraphPoints = params.defaultNumDemographicGraphPoints;
            }

            long populationSeed = m_random.nextLong();
            m_population = new Population(populationSeed, populationParams);

        }
        
        public void Train(AITrainingParameters trainParams) {
            
            for(int epoch = 0; epoch < trainParams.numEpochs; ++epoch) {

                m_population.Train(trainParams.populationTrainingParameters);

                boolean shouldPrintStats = ((epoch % trainParams.outputStride) == 0);
                if(shouldPrintStats) {

                    System.out.printf("[E: %4d]\n", epoch);

                    // Result parent1Results = algorithmResults[bestAlgorithmIndex];

                    // double batchNormalizer   = 1.0 / batchSize;
                    // double parent1Avgfitness = parent1Results.total.m_fitness * batchNormalizer;
                    // double parent1AvgGame    = parent1Results.total.m_gameScore * batchNormalizer;
                    // double parent1AvgMaxTile = parent1Results.total.m_gameMaxTile * batchNormalizer;
                    // double parent1AvgMoves   = parent1Results.total.m_gameMoves * batchNormalizer;

                    // System.out.printf("[E: %4d - %2d, A: %3d] | AVG: [F: %8.02f, G: %7.02f, T: %7.02f, M: %7.02f] | MIN: [F: %8.02f, G: %5d, T: %4d, M: %4d] | MAX: [F: %8.02f, G: %5d, T: %4d, M: %4d]\n",
                    //     epoch, t, bestAlgorithmIndex,
                    //     parent1Avgfitness, parent1AvgGame, parent1AvgMaxTile, parent1AvgMoves,
                    //     parent1Results.min.m_fitness, parent1Results.min.m_gameScore, parent1Results.min.m_gameMaxTile, parent1Results.min.m_gameMoves,
                    //     parent1Results.max.m_fitness, parent1Results.max.m_gameScore, parent1Results.max.m_gameMaxTile, parent1Results.max.m_gameMoves
                    // );
                }
            }
        
            System.out.println("DONE TRAINING!");
        }

        public void PlayTests(int numDemos, int demoDelayMs) {
            
            for(int i = 0; i < numDemos; ++i) {
                Game game = new Game(m_random.nextLong());
                game.Show("Test - "+i);

                // TODO: THIs!
                // bestAlgorithm.PlayGame(game, demoDelayMs);
            }
        }        
    }

    public static void main(String[] args) {

        AIParameters aiParameters = new AIParameters(){{

            seed = 8264;

            // defaultNumThreads = 1;
            defaultNumThreads = 32;

            // TODO: these should default to aiTrainingParams numEpochs and populationTrainingsPerDemographics
            defaultNumPopulationGraphPoints = 1000;
            defaultNumDemographicGraphPoints = 5 * defaultNumPopulationGraphPoints;

            populationParameters = new PopulationParameters(){{
                
                numDemographics = 3;
    
                demographicParameters = new DemographicParameters(){{
                    layerWidths     = new int[]{8, 4, 4};
                    // layerWidths     = new int[]{32, 16, 4};
                    // layerWidths     = new int[]{64, 32, 4};
                    // numAlgorithms   = 1000;
                    numAlgorithms   = 200;
                    // numAlgorithms   = 2000;

                    // trainingSetSize = 3;
                    trainingSetSize = 5;
                }};                
            }};
        }};

        AITrainingParameters aiTrainingParams = new AITrainingParameters(){{
            
            numEpochs    = 1000;
            // numEpochs    = 10;
            outputStride = 1;

            populationTrainingParameters = new PopulationTrainingParameters(){{            
                trainingsPerDemographic = 5;

                int numDemographicAlgorithms = aiParameters.populationParameters.demographicParameters.numAlgorithms;

                migrationCount          = (int)(.10 * numDemographicAlgorithms);
                migrationResistantCount = (int)(.01 * numDemographicAlgorithms);

                crossbreedCount         = (int)(.10 * numDemographicAlgorithms);
                crossbreedPoolSize      = (int)(.10 * numDemographicAlgorithms);
                crossbreedMutationRate  = 0;
                crossbreedMutationRange = 1;

                demographicTrainingParameters = new DemographicTrainingParameters() {{
                 
                    // batchSize = 3;
                    batchSize = 5;

                    survivalCount           = (int)(.10 * numDemographicAlgorithms);
                    mutationCount           = (int)(.05 * numDemographicAlgorithms);
                    extinctionSurvivalCount = (int)(.01 * numDemographicAlgorithms);

                    crossoverPoolSize       = Math.max(1, survivalCount);
                    // crossoverPoolSize       = (int)(.20 * numDemographicAlgorithms);

                    luckyPoolSize      = (int)(.01 * numDemographicAlgorithms);
                    luckyRate          = .1;
                    luckyMutationRate  = .1; 
                    luckyMutationRange = 1;

                    extinctionRate = .005;
                
                    mutationRate  = .05;
                    // mutationRate  = .02;
                    mutationRange = 1;
                    
                    crossoverMutationRate  = .1;
                    // crossoverMutationRate  = .05;
                    crossoverMutationRange = 1;                
                }};
            }};         

        }};

        AI ai = new AI(aiParameters);

        ai.Train(aiTrainingParams);

        // Exit for easier profiling
        // System.exit(0);
        
        // TODO: run games
        // // show a game using best model
        // int algorithmIndex = sortedAlgorithmIndices[0];
        // GeneticAlgorithm algorithm = algorithms[algorithmIndex];

        // // run ai on last training demos
        // int trainingDemoSize = min();
        // for(int i = 0; i < trainingDemoSize; ++i) {
        //     String title = "Training Demo: "+i;

        //     // pull game seed from last trained batch which should perform the best
        //     int trainingIndex = batchTrainingIndices[trainingSetSize - 1];
        //     long gameSeed = trainingGameSeeds[trainingIndex];

        //     PlayDemo(title, algorithm.m_network, gameSeed, demoDelayMs);
        // }

        // // run ai on new demos
        // random.setSeed(9867);
        // for(int i = 0; i < testDemoSize; ++i) {
        //     String title = "Test Demo: "+i;
        //     PlayDemo(title, algorithm.m_network, random.nextLong(), demoDelayMs);
        // }

    }
}