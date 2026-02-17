import java.util.Random;

import java.awt.Color;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Rectangle;
import java.awt.event.*;

public class Game {
    
    public static final int kBoardWidth  = 4;
    public static final int kBoardHeight = 4;
    public static final int kBoardSize = kBoardWidth * kBoardHeight;
    public static final int kBlankTile = 0;
    
    public enum Direction { UP, DOWN, LEFT, RIGHT };

    protected int[] m_board = new int[kBoardSize];
    protected int m_numTiles = 0;

    protected Random m_random;
    protected long m_startTime = 0;
    protected long m_stopTime = 0;
    protected int m_score = 0;
    protected int m_maxTile = 0;
    protected int m_numMoves = 0;
    protected Direction m_lastMove = null;
        
    protected static class Frame extends AppFrame {

        public int m_padding = 10;
        public int m_statusBarHeight = 40;
        public double m_tileRadiusRatio = .1;
        public double m_targetFrameTime = 1/60;

        protected Game m_game;

        public Frame(Game game, String name) {
            super((name == null) ? "2048" : ("2048 - "+name), 420, 500);
            
            m_game = game;
            
            addKeyListener(new KeyAdapter(){
                @Override
                public void keyPressed(KeyEvent e) {

                    switch(e.getKeyCode()) {
                        case KeyEvent.VK_ESCAPE: m_game.Hide();
                        break;

                        case KeyEvent.VK_RIGHT: m_game.Move(Direction.RIGHT);    
                        break;
                    
                        case KeyEvent.VK_LEFT: m_game.Move(Direction.LEFT);    
                        break;

                        case KeyEvent.VK_UP: m_game.Move(Direction.UP);    
                        break;

                        case KeyEvent.VK_DOWN: m_game.Move(Direction.DOWN);    
                        break;
                    }
                }
            });
        }

        public void Draw() {

            Graphics graphics = m_bufferStrategy.getDrawGraphics();

            graphics.setFont(m_font);
            FontMetrics fontMetrics = graphics.getFontMetrics();

            Rectangle rootRect = m_rootPane.getBounds();
            Rectangle contentRect = m_contentPane.getBounds();

            graphics.clearRect(rootRect.x, rootRect.y, contentRect.width, contentRect.height);

            // draw statusBar
            String scoreString = "Score: " + String.valueOf(m_game.m_score) + " ["+m_game.m_maxTile+" | "+String.valueOf(m_game.m_numTiles)+"/"+String.valueOf(kBoardSize)+"]";
            
            if(m_game.m_lastMove != null) {
                scoreString+= " "+m_game.m_lastMove.name();
            }
            
            if(m_game.IsGameOver()) {
                scoreString+= m_game.m_maxTile < 2048 ? " You Lose!" : " You Win!";
            }
            
            String timeString = "Time: " + String.format("%.2f", m_game.ElapsedTime());
        
            int statusBarTextY = rootRect.y + m_padding + m_font.getSize();
            int scoreStringX = rootRect.x + m_padding;
            int timeStringX = rootRect.x + contentRect.width - (m_padding + fontMetrics.stringWidth(timeString));
            
            graphics.setColor(Color.WHITE);
            graphics.drawString(scoreString, scoreStringX, statusBarTextY);
            graphics.drawString(timeString, timeStringX, statusBarTextY);

            // draw board
            int maxBoardWidth  = contentRect.width - 2*m_padding;
            int maxBoardHeight = contentRect.height - (m_statusBarHeight + 3*m_padding);

            int maxTileStrideX = (maxBoardWidth  - m_padding) / kBoardWidth;
            int maxTileStrideY = (maxBoardHeight - m_padding) / kBoardHeight;
            
            int tileStride = (maxTileStrideX < maxTileStrideY) ? maxTileStrideX : maxTileStrideY;
            int tileSize   = Math.max(tileStride - m_padding, 12);
            int tileArc    = (int)(m_tileRadiusRatio * tileSize);

            int boardX      = rootRect.x + m_padding;
            int boardY      = statusBarTextY + m_statusBarHeight;
            int boardWidth  = tileStride * kBoardWidth  + m_padding;
            int boardHeight = tileStride * kBoardHeight + m_padding;

            graphics.drawRect(boardX, boardY, boardWidth, boardHeight);

            for(int y = 0; y < kBoardHeight; ++y) {

                for(int x = 0; x < kBoardWidth; ++x) {
                    int tile = m_game.GetTile(x, y);
                    if(tile == kBlankTile) continue;

                    // draw the tile
                    int tileX = boardX + m_padding + x * tileStride;
                    int tileY = boardY + m_padding + y * tileStride;

                    String tileText = String.valueOf(tile);
                    int tileTextWidth = fontMetrics.stringWidth(tileText);
                    
                    graphics.setColor(Color.RED);
                    graphics.drawRoundRect(tileX, tileY, tileSize, tileSize, tileArc, tileArc);
                    
                    graphics.setColor(Color.WHITE);
                    graphics.drawString(tileText, tileX + (tileSize - tileTextWidth)/2, tileY + tileSize/2);
                }

            }
            
            m_bufferStrategy.show();
        }
    };

    public Frame m_shownFrame = null;

    public Game(long randomSeed) {
        m_random = new Random(randomSeed);
    
        // initialize board with tiles
        SpawnTile(2);
        SpawnTile(2);
    }

    public Double ElapsedTime() {
        if(m_stopTime != 0) {
            // game terminated
            return (1e-9 * (m_stopTime - m_startTime));
        }

        // game is running
        return m_startTime == 0 ? 0 : (1e-9 * (System.nanoTime() - m_startTime));
    }

    public int GetTile(int x, int y) {
        if(x < 0 || x >= kBoardWidth || y < 0 || y >= kBoardHeight) {
            return kBlankTile;
        }
        return m_board[y*kBoardWidth + x];        
    }

    public int SpawnTile() {
        return SpawnTile(m_random.nextFloat() < .9 ? 2 : 4);
    }

    public int SpawnTile(int spawnValue) {

        if(m_numTiles >= kBoardSize) return -1;

        int numFreeTiles = kBoardSize - m_numTiles;
        int freeTileOffset = Math.abs(m_random.nextInt()) % numFreeTiles;

        for(int i = 0; i < kBoardSize; ++i) {
            if(m_board[i] == kBlankTile) {

                if(freeTileOffset == 0) {

                    // spawn here
                    m_board[i] = spawnValue;
                    ++m_numTiles;
                    return i;
                }
                
                --freeTileOffset;
            }
        }

        assert false : "Unreachable";
        return -1;
    }

    protected int SlideTile(int tileIndex, int wallIndex, int wallStride) {
        int tile = m_board[tileIndex];
        if(tile != kBlankTile) {

            // pick up tile
            m_board[tileIndex] = kBlankTile;
            
            int wallTile = m_board[wallIndex];
            if(wallTile == tile) {
            
                // merge tile with wallTile
                tile*= 2;
                --m_numTiles;

                m_score+= tile;

                if(tile > m_maxTile) {
                    m_maxTile = tile;
                }
                
            } else if(wallTile != kBlankTile) {

                // move tile next to wallTile
                wallIndex+= wallStride;
            }

            // put down tile
            m_board[wallIndex] = tile;
        }

        return wallIndex;
    }

    protected void SlideTiles(Direction direction) {

        if(direction == Direction.RIGHT || direction == Direction.LEFT) {

            int xStart, xEnd, xStride;
            if(direction == Direction.LEFT) {
                xStart  = 0;
                xEnd    = kBoardWidth;
                xStride = 1;

            } else {
                xStart  = kBoardWidth - 1;
                xEnd    = -1;
                xStride = -1;
            }

            for(int y = 0; y < kBoardHeight; ++y) {
                int yIndexOffset = y * kBoardWidth;
                
                int wallIndex = yIndexOffset + xStart;
                for(int x = xStart; x != xEnd; x+= xStride) {
                
                    int tileIndex = yIndexOffset + x;    
                    wallIndex = SlideTile(tileIndex, wallIndex, xStride);
                }
            }
        } else {

            int yStart, yEnd, yStride, wallStride;
            if(direction == Direction.UP) {
                yStart     = 0;
                yEnd       = kBoardHeight;
                yStride    = 1;
                wallStride = kBoardWidth;

            } else {
                yStart     = kBoardHeight - 1;
                yEnd       = -1;
                yStride    = -1;
                wallStride = -kBoardWidth;     
            }

            for(int x = 0; x < kBoardWidth; ++x) {

                int wallIndex = yStart * kBoardWidth + x;
                for(int y = yStart; y != yEnd; y+= yStride) {

                    int tileIndex = y * kBoardWidth + x;
                    wallIndex = SlideTile(tileIndex, wallIndex, wallStride);
                }
            }
        }
    }

    public boolean Move(Direction direction) {

        if(m_stopTime != 0) {
            // game is terminated
            return false;
        }

        if(m_startTime == 0) {
            m_startTime = System.nanoTime();
        }

        int oldScore = m_score;

        SlideTiles(direction);
        int spawnedIndex = SpawnTile();        
        
        if(IsGameOver()) {
            m_stopTime = System.nanoTime();
        }

        m_lastMove = direction;

        // failed to move if the score doesn't change and we can't spawn new tile
        boolean madeMove = (oldScore != m_score || spawnedIndex != -1);
        if(madeMove) {
            ++m_numMoves;
        }
        
        return madeMove;
    }

    public boolean IsGameOver() {

        // check if game already terminated
        if(m_stopTime != 0) return true;

        // check if we can move to blank space
        if(m_numTiles != kBoardSize) return false;

        // check if we can merge tiles
        for(int y = 0; y < kBoardHeight; ++y) {
            int yIndexOffset = y*kBoardWidth;

            for(int x = 0; x < kBoardWidth; ++x) {
                int tileIndex = yIndexOffset + x;
                int tile = m_board[tileIndex];
                
                // check if we can merge right / left
                if(x < (kBoardWidth-1)) {
                    int rightTile = m_board[tileIndex + 1];
                    if(tile == rightTile) return false;
                }
                
                // check if we can merge up / down
                if(y < (kBoardHeight-1)) {
                    int lowerTile = m_board[tileIndex + kBoardWidth];
                    if(tile == lowerTile) return false;
                }
            }
        }
        
        // no valid move
        return true;
    }

    public void Show(String name) {
        if(m_shownFrame != null) return;
        m_shownFrame = new Frame(this, name);
        m_shownFrame.setAlwaysOnTop(true);
    }

    public void Hide() {
        if(m_shownFrame == null) return;
        m_shownFrame.Close();
        m_shownFrame = null;
    }
}