import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.GridLayout;
import java.awt.Rectangle;
import java.util.ArrayList;
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

            return Math.tanh(weightedInput);
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
        protected int m_outputSize;
        protected int m_maxNumLayerWeights;

        protected static class ThreadState {
            // Note: m_threadSafeLayerOutput needs to be large enough to store input and output partial results
            public double[] layerOutput;
            public double[] evalResults; 

            public ThreadState(Network network) {
                layerOutput = new double[2*network.m_maxNumLayerWeights];
                evalResults = new double[network.m_outputSize];
            }

        }

        ThreadLocal<ThreadState> m_threadState = ThreadLocal.withInitial(() -> new ThreadState(this));

        public Network(int inputSize, int[] layerWidths, Random random) {

            int numLayers = layerWidths.length;
            assert numLayers > 0: "Invalid numLayers. Expected pos number got: "+numLayers;

            m_layers = new Layer[numLayers];
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

        public double[] EvalThreadSafe(double[] inputs) {
            
            ThreadState threadState = m_threadState.get();

            double[] results = threadState.evalResults;
            double[] outputs = threadState.layerOutput;
            
            // eval intermediate layers into outputs
            // Note: we offset the input and output because we cannot call Eval with same input and output location.
            //       If we did input will be partialally overwritten during neuron eval calls
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
            //       and update relavent indicies as needed. Values are initialized for a 1 hot encoding for last output layer
            int outputSize = m_network.m_outputSize;
            int significancesStride = m_network.m_maxNumLayerWeights * outputSize;
            double[] significances = new double[2 * significancesStride];
            for(int i = 0; i < outputSize; ++i) {
                significances[i*outputSize + i] = 1;
            };
            
            // Note: we draw layers in reverse order to allow us to backpropigate significance
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

                // zero initialize input signifcances
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

                        // update input neuron signficance
                        int inputSignificanceOffset = inputLayerSignificanceOffset + i*outputSize;
                        for(int o = 0; o < outputSize; ++o) {
                            double outputSignficance = significances[neuronSignificanceOffset + o];
                            significances[inputSignificanceOffset + o]+= outputSignficance * weightSignificance;
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
            double cursorY = (m_cursorIndex > m_dataStartIndex) ? m_data[m_cursorIndex] : 0;
            String graphTitle = String.format("%s [%.01f, %.01f]: (%d, %.01f)", m_name, m_yMin, m_yMax, cursorX, cursorY);                

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

        public static final int kDeafultWindowWidth = 600;
        public static final int kDefaultWindowHeight = 300;
        
        public static final int kDefaultGraphWidth  = (int)(kDeafultWindowWidth * .4 + .5);
        public static final int kDefaultGraphHeight = 50;

        protected GridLayout m_networkContainerLayout = new GridLayout(1,1);
        protected JPanel m_networkContainer = new JPanel(m_networkContainerLayout);

        protected GraphPane m_graphPane = new GraphPane();

        
        public NetworkGUI(String title) {
            super(title, kDeafultWindowWidth, kDefaultWindowHeight);

            m_contentPane.setLayout(new BoxLayout(m_contentPane, BoxLayout.X_AXIS));

            m_contentPane.add(m_networkContainer);
            m_contentPane.add(m_graphPane);

            m_networkContainer.setPreferredSize(new Dimension(kDeafultWindowWidth - kDefaultGraphWidth, kDefaultWindowHeight));
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

        public Network m_network;
        public Random m_random;

        public static final Game.Direction[] kDirections = Game.Direction.values();

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

        public double PlayGame(Game game, int msDelay, boolean threadSafe) {
        
            double[] inputs = new double[Game.kBoardSize];
            int[] sortedResultIndices = new int[kDirections.length];

            while(!game.IsGameOver()) {

                // get board input
                for(int i = 0; i < inputs.length; ++i) {
                    int tile = game.m_board[i];

                    // Normalized input for the largest possible tile value of 131,072 = 2^17
                    int tileBits = GetHighestBit(tile);
                    inputs[i] = tileBits * (1/17.0);
                }
                
                // evaluate network
                double[] results = threadSafe ? m_network.EvalThreadSafe(inputs) : m_network.Eval(inputs);
                
                // Sort results only 4 results, this insertion sort should be fast
                SortIndices(results, sortedResultIndices);

                // make best move
                for(int i = 0; i < sortedResultIndices.length; ++i) {
                    int directionIndex = sortedResultIndices[i];

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

    public static abstract class GameWorker implements Callable<Object> {
        int m_id;
        GameWorkerResult m_result = new GameWorkerResult();

        public GameWorker(int id) {            
            m_id = id;
        }
    
        public Object PlayGame(long gameSeed, GeneticAlgorithm algorithm) {
            Game game = new Game(gameSeed);            
            double fitness = algorithm.PlayGame(game, 0, true);
            
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

        public static <T extends GameWorker> void Sort(ArrayList<T> gameWorkers) {
            // sort m_algorithmWorkers in descending order by results
            
            // TODO: Make this the standard comparison of GameWorkerResult
            gameWorkers.sort((GameWorker worker1, GameWorker worker2) -> {
                
                GameWorkerResult results1 = worker1.m_result;
                GameWorkerResult results2 = worker2.m_result;
                
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
            });
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
        GeneticAlgorithm m_algorithm;
        LongPtr m_gameSeedPtr;

        public DemographicGameWorker(int id, GeneticAlgorithm algorithm, LongPtr gameSeedPtr) {
            super(id);
            m_algorithm   = algorithm;
            m_gameSeedPtr = gameSeedPtr;
        }

        @Override
        public Object call() {
            return PlayGame(m_gameSeedPtr.value, m_algorithm);
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

        double luckRate;
        double extinctionRate;
    
        double mutationRate;
        double mutationRange;
        
        int    crossoverPoolSize;        
        double crossoverMutationRate;
        double crossoverMutationRange;

    }

    public static class Demographic {
        Random m_random;
        DemographicParameters m_parameters;

        GeneticAlgorithm[] m_algorithms;
        Integer[] m_algorithmIndices;

        long[] m_trainingSeeds;
        int[] m_batchTrainingIndices;

        ArrayList<DemographicGameWorker> m_gameWorkers;
        LongPtr m_workerTrainingSeedPtr = new LongPtr();
        boolean m_isGameWorkersSorted = false;

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
                
                m_gameWorkers.add(new DemographicGameWorker(i, algorithm, m_workerTrainingSeedPtr));
            }
        }

        public void SortGameWorkers() {

            // Lazy sorting to speed up training in inner loops
            if(!m_isGameWorkersSorted) {
                GameWorker.Sort(m_gameWorkers);
                m_isGameWorkersSorted = true;
            }
        }

        public DemographicGameWorker GetBestGameWorker() {
            
            // TODO: only invoke for dity algorithms and batches!  
            GameWorker.ClearResults(m_gameWorkers);
            InvokeBatch(m_parameters.threadPool, 0, m_parameters.trainingSetSize, m_trainingSeeds);
            SortGameWorkers();

            return m_gameWorkers.getFirst();
        }

        protected int CreateRandomBatch(int batchSize) {
            // Computes a random batch of 'batchSize' training from m_batchTrainingIndicies
            // the random indices are placed at the end of the m_batchTrainingIndicies array
            // Returns the first index of batch in m_batchTrainingIndicies 
            // Requires 'batchSize' in range [0, m_batchTrainingIndicies.length]
            
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
            
            return m_batchTrainingIndices.length - batchSize;
        }

        public void InvokeBatch(ExecutorService threadPool, int batchStartIndex, int batchSize, long[] gameSeeds) {
            if(batchSize <= 0) return;

            m_isGameWorkersSorted = false;
            for(int i = 0; i < batchSize; ++i) {
                
                // Evaluate all algorithms with same game batch seed
                int trainingIndex = m_batchTrainingIndices[batchStartIndex + i];
                m_workerTrainingSeedPtr.value = gameSeeds[trainingIndex];
                
                GameWorker.Invoke(threadPool, m_gameWorkers);
            }
        }

        public void Train(DemographicTrainingParameters trainParams) {
            
            // evaluate a new random batch
            int batchSize = Math.min(m_batchTrainingIndices.length, trainParams.batchSize);
            int batchStartIndex = CreateRandomBatch(batchSize);
            
            // TODO: HERE!!! - rather than clearing the results each time
            //       track which algorithms are dirty and which batches have been already invoked!
            GameWorker.ClearResults(m_gameWorkers);
            InvokeBatch(m_parameters.threadPool, batchStartIndex, batchSize, m_trainingSeeds);
            
            // sort m_gameWorkers to partition them into surviving / crossover / mutation groups
            SortGameWorkers();
            
            // evolve algorithms 
            boolean isExtinction = (m_random.nextDouble() < trainParams.extinctionRate);
            if(isExtinction) {

                // replace all nonsurviviors with new networks
                for(int i = trainParams.extinctionSurvivalCount; i < m_parameters.numAlgorithms; ++i) {
                    DemographicGameWorker worker = m_gameWorkers.get(i);
                    worker.m_algorithm.Reset();
                }
            
            } else {
                // Normal training
                int crossoverIndex = trainParams.survivalCount + trainParams.mutationCount;
                DemographicGameWorker bestWorker = m_gameWorkers.get(0);

                // Update all non surviving algorithms
                for(int i = trainParams.survivalCount; i < m_parameters.numAlgorithms; ++i) {
                    
                    DemographicGameWorker worker = m_gameWorkers.get(i);
                    GeneticAlgorithm algorithm   = worker.m_algorithm;

                    boolean isLucky = m_random.nextDouble() < trainParams.luckRate;
                    if(isLucky) {

                        // congrats! make a child with the best algorithm
                        algorithm.MakeChild(algorithm, bestWorker.m_algorithm, trainParams.crossoverMutationRate, trainParams.crossoverMutationRange); 

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

            // TODO: mark mutated algorithms dirty!
            m_isGameWorkersSorted = false;
        }
    }

    public static class PopulationParameters {
        int numDemographics;
        int numGraphPoints;
        
        // TODO: THIS SHOULD BE PULLED OUT TO AI PARAMETERS!!!
        int validationSetSize = 10;
        
        DemographicParameters demographicParameters;
        ExecutorService threadPool;
    }

    public static class PopulationTrainingParameters {
        DemographicTrainingParameters demographicTrainingParameters;
        
        int trainingsPerDemographic;

        int migrationCount;
        int migrationResistantCount;

        int    crossbreadCount;
        int    crossbreadPoolSize;
        double crossbreadMutationRate;
        double crossbreadMutationRange;
    }

    public static class PopulationGameWorker extends GameWorker {

        Pointer<GeneticAlgorithm> m_algorithmPtr;
        long[] m_gameSeeds;

        public PopulationGameWorker(int id, Pointer<GeneticAlgorithm> algorithmPtr, long gameSeeds[]) {
            super(id);

            m_algorithmPtr = algorithmPtr;
            m_gameSeeds    = gameSeeds;
        }

        @Override
        public Object call() {
            PlayGame(m_gameSeeds[m_id], m_algorithmPtr.value);
            return null;
            // return PlayGame(m_gameSeeds[m_id], m_algorithmPtr.value);
        }
    }

    public static class Population {
        Random m_random;
        PopulationParameters m_parameters;

        Demographic[] m_demographics;

        // TODO: Pull GUI and validation out to AI!
        NetworkGUI m_networkGui;
        long[] m_validationGameSeeds;


        // Note: 1 network and graph panel for each demographic and +1 for validation
        GraphPanel[] m_graphPanels;
        NetworkPanel[] m_networkPanels;
        ArrayList<PopulationGameWorker>[] m_gameWorkerArrays;

        Pointer<GeneticAlgorithm> m_gameWorkerAlgorithmPtr = new Pointer<>();        

        public Color m_forgroundColor  = Color.lightGray;
        public Color m_backgroundColor = Color.gray;


        public Population(long randomSeed, PopulationParameters params) {
            m_random     = new Random(randomSeed);
            m_parameters = params; 

            // TODO: Move GUI somewhere else? Like AI?
            {
                m_networkGui = new NetworkGUI("Population Networks");
                m_validationGameSeeds = new long[params.validationSetSize];
                for(int i = 0; i < params.validationSetSize; ++i) {
                    m_validationGameSeeds[i] = m_random.nextLong();
                }
            }

            m_demographics     = new Demographic[params.numDemographics];

            // +1 for cumulative population stats
            int numGUIItems = params.numDemographics + 1;
            m_graphPanels      = new GraphPanel[numGUIItems];
            m_networkPanels    = new NetworkPanel[numGUIItems];
            m_gameWorkerArrays = new ArrayList[numGUIItems];

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
            for(int i = 0; i < numGUIItems; ++i) {
                
                String guiItemName;
                Color guiItemColor;
                ArrayList<PopulationGameWorker> gameWorkers;

                int demographicTrainingSetSize = params.demographicParameters.trainingSetSize;

                if(i < params.numDemographics) {

                    // create demographic
                    long demographicSeed = m_random.nextLong();
                    Demographic demographic = new Demographic(demographicSeed, params.demographicParameters);
                    m_demographics[i] = demographic;
                    
                    // create game workers for demographic
                    gameWorkers = new ArrayList<>(demographicTrainingSetSize);
                    for(int j = 0; j < demographicTrainingSetSize; ++j) {
                        gameWorkers.add(new PopulationGameWorker(j, m_gameWorkerAlgorithmPtr, demographic.m_trainingSeeds));
                    }

                    guiItemName  = "D-" + i;
                    guiItemColor = m_backgroundColor;
                    
                } else {

                    // TODO: create game workers for whole population not validation seeds?
                    gameWorkers = new ArrayList<>(params.validationSetSize);
                    for(int j = 0; j < params.validationSetSize; ++j) {
                        gameWorkers.add(new PopulationGameWorker(j, m_gameWorkerAlgorithmPtr, m_validationGameSeeds));
                    }

                    guiItemName  = "Validation";
                    guiItemColor = Color.CYAN;
                }


                m_gameWorkerArrays[i] = gameWorkers;

                // create networkPanel
                NetworkPanel networkPanel = m_networkGui.AddNetworkPanel(guiItemName, null, inputNames, outputNames, outputColors);
                networkPanel.m_nameColor = guiItemColor;
                m_networkPanels[i] = networkPanel;

                // create graph
                if(params.numGraphPoints > 0) {
                    double[] graphData = new double[params.numGraphPoints];

                    GraphPanel graph = m_networkGui.AddGraph(guiItemName, params.numGraphPoints, graphData, 0, 0);

                    graph.m_xMin = 0;
                    graph.m_xMax = params.numGraphPoints;
                    
                    // Note: initilized reversed so graph scales on first update no mater fitness
                    graph.m_yMin = Double.MAX_VALUE;
                    graph.m_yMax = Double.MIN_VALUE;

                    graph.m_mode  = GraphMode.SCROLL;
                    graph.m_color = guiItemColor;

                    m_graphPanels[i] = graph;
                }
            }
        }

        // TODO: should this return a GameWorker so we also have the performance of it?
        public GeneticAlgorithm Train(PopulationTrainingParameters trainParams) {

            // train each demographic
            for(int i = 0; i < m_parameters.numDemographics; ++i) {
                
                // TODO: Pack this into class to make things cleaner
                //       we could also move the plotting logic there?
                Demographic demographic   = m_demographics[i];
                GraphPanel graphPanel     = m_graphPanels[i];
                NetworkPanel networkPanel = m_networkPanels[i];
                ArrayList<PopulationGameWorker> gameWorkers = m_gameWorkerArrays[i];

                graphPanel.m_color = m_forgroundColor;
                networkPanel.m_nameColor = m_forgroundColor;

                for(int t = 0; t < trainParams.trainingsPerDemographic; ++t) {
                
                    demographic.Train(trainParams.demographicTrainingParameters);
                    
                    DemographicGameWorker bestWorker = demographic.GetBestGameWorker();
                    GeneticAlgorithm bestAlgorithm   = bestWorker.m_algorithm;

                    // TODO: output batch results?
                    
                    // TODO: Do we need to copy weights for multithreading?
                    networkPanel.m_network = bestAlgorithm.m_network;

                    double avgTrainingSetFitness = bestWorker.m_result.total.m_fitness / m_parameters.demographicParameters.trainingSetSize;
                    graphPanel.pushPoint(avgTrainingSetFitness, true);
                    
                    // TODO: HERE!!! --- there is a disconnect between bestWorker.m_result.total.m_fitness
                    m_gameWorkerAlgorithmPtr.value = bestAlgorithm;

                    GameWorker.ClearResults(gameWorkers);
                    GameWorker.Invoke(m_parameters.threadPool, gameWorkers);
                    GameWorkerResult cumulativeResult = GameWorker.GetCumulativeResult(gameWorkers);

                    // TODO: Plot min & max on same graph too!

                    double error = bestWorker.m_result.total.m_fitness - cumulativeResult.total.m_fitness;
                    if(Math.abs(error) > 1E10) {
                        System.out.println("OH NO!!");
                    }
                }

                graphPanel.m_color = m_backgroundColor;
                networkPanel.m_nameColor = m_backgroundColor;
            }

            // TODO: CLEAN THIS UP!!!

            // crossbread
            for(int i = 0; i < m_parameters.numDemographics; ++i) {
                Demographic demographic1 = m_demographics[i];
                
                for(int j = 0; j < trainParams.crossbreadCount; ++j) {

                    int demographic2Index = m_random.nextInt(m_parameters.numDemographics);
                    Demographic demographic2 = m_demographics[demographic2Index];
                    
                    // select worst performer as a child
                    int childIndex   = demographic1.m_parameters.numAlgorithms - i - 1;

                    // sample best performers for parents
                    int parentIndex1 = m_random.nextInt(trainParams.crossbreadPoolSize);
                    int parentIndex2 = m_random.nextInt(trainParams.crossbreadPoolSize);

                    // mingle
                    DemographicGameWorker parentWorker1 = demographic1.m_gameWorkers.get(parentIndex1);
                    DemographicGameWorker parentWorker2 = demographic2.m_gameWorkers.get(parentIndex2);
                    DemographicGameWorker childWorker   = demographic2.m_gameWorkers.get(childIndex);

                    GeneticAlgorithm parent1 = parentWorker1.m_algorithm; 
                    GeneticAlgorithm parent2 = parentWorker2.m_algorithm; 
                    GeneticAlgorithm child   = childWorker.m_algorithm; 

                    child.MakeChild(parent1, parent2, trainParams.crossbreadMutationRate, trainParams.crossbreadMutationRange);
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

                    Network network1 = algorithm1.m_network;
                    Network network2 = algorithm2.m_network;

                    algorithm1.m_network = network2;
                    algorithm2.m_network = network1;
                }    
            }
            
            // TODO: find best population network and plot validation data
            // TODO: HIZZLE ---- Make this work. Validation data should probably be in the main AI class
            //       we should really be selecting the top performing algorithm from the union of our population's training set?
            //       however we should prioritize returning something so we can actually play a demo of the top algorithm!
            NetworkPanel                    validationNetworkPanel = m_networkPanels[m_parameters.numDemographics];
            GraphPanel                      validationGraphPanel   = m_graphPanels[m_parameters.numDemographics];
            ArrayList<PopulationGameWorker> validationGameWorkers  = m_gameWorkerArrays[m_parameters.numDemographics];

            GeneticAlgorithm bestValidationAlgorithm = null;
            GameWorkerResult bestValidationResults = new GameWorkerResult();
            for(int i = 0; i < m_parameters.numDemographics; ++i) {
                Demographic demographic = m_demographics[i];
                DemographicGameWorker bestDemographicGameWorker = demographic.m_gameWorkers.get(0);

                // // TODO: this is hacky.. should we evaluate all demographic algorithms not just their best?
                // //       also, should we have a different GameWorker that can run everything together?
                // //       we could also just Eval the demographic on our validation game seeds?
                // m_gameWorkerAlgorithmPtr.value = bestDemographicGameWorker.m_algorithm;
                // GameWorker.ClearResults(validationGameWorkers);
                // GameWorker.Invoke(trainParams.threadPool, validationGameWorkers);
                // GameWorkerResult cumulativeResult = GameWorker.GetCumulativeResult(validationGameWorkers);                

                // if(cumulativeResult.total.m_fitness > bestValidationResults.total.m_fitness || cumulativeResult.min.m_fitness > bestValidationResults.min.m_fitness) {
                //     bestValidationResults = cumulativeResult;
                //     bestValidationAlgorithm = bestDemographicGameWorker.m_algorithm;
                // }


                // DemographicGameWorker validationGameWorker = demographic.EvaluateBatch(
                //     demographic.m_parameters.threadPool, 
                //     0, demographic.m_parameters.trainingSetSize, 
                //     m_validationGameSeeds
                // );
                // GameWorkerResult validationResult = validationGameWorker.m_result;

                // // TODO: rely on GameWorker.Sort to generate this so we have an ordering!
                // if(validationResult.total.m_fitness > bestValidationResults.total.m_fitness || validationResult.min.m_fitness > bestValidationResults.min.m_fitness) {
                //     bestValidationResults = validationResult;
                //     bestValidationAlgorithm = bestDemographicGameWorker.m_algorithm;
                // }
                
            }

            // double bestValidationAvgFitness = bestValidationResults.total.m_fitness / m_parameters.validationSetSize;
            // validationNetworkPanel.m_network = bestValidationAlgorithm.m_network;
            // validationGraphPanel.pushPoint(bestValidationAvgFitness, true);
    
            return bestValidationAlgorithm;
        }

    }

    public static class AIParameters {
        int defaultNumThreads;

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
        
        public AI(long seed, AIParameters params) {
            m_random = new Random(seed);

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


            long populationSeed = m_random.nextLong();
            m_population = new Population(populationSeed, populationParams);            
        
            m_population.m_networkGui.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
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
            defaultNumThreads = 32;

            populationParameters = new PopulationParameters(){{
                
                numDemographics = 3;
    
                demographicParameters = new DemographicParameters(){{
                    layerWidths     = new int[]{8, 4, 4};
                    numAlgorithms   = 1000;

                    trainingSetSize = 3;
                    // trainingSetSize = 2;
    
                    // numGraphPoints = 1000;
                    numGraphPoints = 10 * 250;
                }};                
            }};
        }};

        AITrainingParameters aiTrainingParams = new AITrainingParameters(){{
            
            numEpochs    = 250;
            outputStride = 1;

            populationTrainingParameters = new PopulationTrainingParameters(){{            
                trainingsPerDemographic = 10;

                int numDemographicAlgorithms = aiParameters.populationParameters.demographicParameters.numAlgorithms;

                migrationCount          = (int)(.10 * numDemographicAlgorithms);
                migrationResistantCount = (int)(.01 * numDemographicAlgorithms);

                crossbreadCount         = (int)(.10 * numDemographicAlgorithms);
                crossbreadPoolSize      = (int)(.10 * numDemographicAlgorithms);
                crossbreadMutationRate  = 0;
                crossbreadMutationRange = 1;

                demographicTrainingParameters = new DemographicTrainingParameters() {{
                 
                    // batchSize = 3;
                    batchSize = 2;
                    // batchSize = 2;

                    survivalCount           = (int)(.10 * numDemographicAlgorithms);
                    mutationCount           = (int)(.05 * numDemographicAlgorithms);
                    extinctionSurvivalCount = (int)(.01 * numDemographicAlgorithms);

                    crossoverPoolSize       = Math.max(1, survivalCount);

                    luckRate       = .01;
                    extinctionRate = 0;
                
                    mutationRate  = .05;
                    mutationRange = 1;
                    
                    crossoverMutationRate  = .1;
                    crossoverMutationRange = 1;                
                }};
            }};         

        }};


        long aiSeed = 8264;
        AI ai = new AI(aiSeed, aiParameters);

        ai.Train(aiTrainingParams);


        
        // TODO: run demos from training set and test sets
        //     // show a game using best model
        //     int algorithmIndex = sortedAlgorithmIndices[0];
        //     GeneticAlgorithm algorithm = algorithms[algorithmIndex];

        //     // run ai on last training demos
        //     for(int i = 0; i < trainingDemoSize; ++i) {
        //         String title = "Training Demo: "+i;

        //         // pull game seed from last trained batch which should perform the best
        //         int trainingIndex = batchTrainingIndicies[trainingSetSize - 1];
        //         long gameSeed = trainingGameSeeds[trainingIndex];

        //         PlayDemo(title, algorithm.m_network, gameSeed, demoDelayMs);
        //     }

        //     // run ai on new demos
        //     random.setSeed(9867);
        //     for(int i = 0; i < testDemoSize; ++i) {
        //         String title = "Test Demo: "+i;
        //         PlayDemo(title, algorithm.m_network, random.nextLong(), demoDelayMs);
        //     }

        //     return;
        // }

    }
}