import java.awt.Color;
import java.awt.Container;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.image.BufferStrategy;

import javax.swing.JFrame;
import javax.swing.Timer;

public class AppFrame extends JFrame {

        public static final double kTargetFrameTime = 1/60;

        protected Timer m_timer;
        protected BufferStrategy m_bufferStrategy;
        protected Font m_font = new Font("consolas", Font.PLAIN, 12);

        protected Container m_contentPane;
        protected Container m_rootPane;

        public AppFrame(String title, int width, int height) {
            super(title);

            m_timer = new Timer((int)(1000*kTargetFrameTime), e -> {
                Draw();
            });
            
            addWindowListener(new WindowAdapter() {
                @Override
                public void windowClosing(WindowEvent e) {
                    Close();
                }
            });

            m_rootPane = getRootPane();
            m_contentPane = getContentPane();
            
            setSize(width, height);
            setBackground(Color.BLACK);
            setVisible(true);

            // Note: window must be visible to get graphics / create buffer startegy
            createBufferStrategy(2);
            m_bufferStrategy = getBufferStrategy();

            m_timer.start();            
        }

        public void Close() {
            m_timer.stop();
            dispose();
        }

        public synchronized void Draw() {
            Graphics graphics = m_bufferStrategy.getDrawGraphics();
            
            paintAll(graphics);

            m_bufferStrategy.show();
        }

}
