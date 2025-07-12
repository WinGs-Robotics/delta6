import threading
import pygame

class ForceVisualizer(threading.Thread):
    """
    A real-time force visualizer using Pygame in a separate thread.
    
    This version supports multiple sets of forces.
    For each set, we have six values: [Fx, Fy, Fz, Mx, My, Mz].
    
    Each of the 6 force components (Fx, Fy, Fz, Mx, My, Mz) is drawn
    in a vertical arrangement, one beneath the other. For each component,
    we stack the bars of different sets. The 'zero' anchor for the bars
    is placed near the center of the screen, so negative values go left,
    and positive values go right. The text labels are pinned on the far left.
    
    Now we also draw a legend in the top-right corner to show which color
    corresponds to which force set name.
    """

    def __init__(self, title="Force Visualizer", width=800, height=600,
                 freq=30, num_sets=1, set_names=None):
        """
        :param title: The window title.
        :param width: Window width in pixels.
        :param height: Window height in pixels.
        :param freq: Refresh rate (frames per second).
        :param num_sets: Number of force sets to display.
        :param set_names: Optional list of names for each force set (length = num_sets).
        """
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.freq = freq  # frames per second

        # We store multiple sets of length-6 forces.
        self.num_sets = num_sets
        self.latest_forces = [[0.0]*6 for _ in range(num_sets)]

        # If user didn't supply set_names, generate default names: "Set 1", "Set 2", ...
        if set_names is not None:
            if len(set_names) != num_sets:
                raise ValueError(
                    f"set_names must have length {num_sets}, but got {len(set_names)}"
                )
            self.set_names = set_names
        else:
            self.set_names = [f"Set {i+1}" for i in range(num_sets)]

        # Thread and Pygame loop control
        self.running = True
        self.daemon = True

        # Visualization scaling
        self.max_length = 200            # Maximum bar length (in pixels)
        self.scale_force = 20.0          # Scale for Fx, Fy, Fz
        self.scale_torque = 500.0          # Scale for Fx, Fy, Fz

        # Colors for each set (extend or reuse if you have more sets)
        self.set_colors = [
            (255, 100, 100),   # Reddish
            (100, 200, 255),   # Light Blue
            (255, 210, 100),   # Orange-ish
            (170, 255, 170),   # Light Green
            (230, 230, 100),   # Yellow-ish
            (240, 160, 240),   # Purple-ish
        ]
        # If num_sets > len(self.set_colors), we may reuse or define more colors.

    def run(self):
        """
        Main loop of the visualizer thread.
        Initializes Pygame, creates a window, and refreshes at the specified FPS.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        clock = pygame.time.Clock()

        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Clear the background
            self.screen.fill((30, 30, 30))

            # Draw the forces
            self.draw_force()

            # (Optional) Draw a small legend in the top-right corner
            self.draw_legend()

            # Update the window
            pygame.display.flip()
            clock.tick(self.freq)

        pygame.quit()

    def stop(self):
        """
        Stop the visualizer thread by setting the running flag to False.
        """
        self.running = False

    def update_forces(self, new_forces):
        """
        Update the latest forces/torques data.
        
        :param new_forces: A list of length `num_sets`, 
                           where each element is [Fx, Fy, Fz, Mx, My, Mz].
                           
        Example:
            If num_sets = 2, new_forces might look like:
            [
              [Fx1, Fy1, Fz1, Mx1, My1, Mz1],
              [Fx2, Fy2, Fz2, Mx2, My2, Mz2]
            ]
        """
        if len(new_forces) != self.num_sets:
            raise ValueError(f"Expected {self.num_sets} sets, but got {len(new_forces)}.")
        
        for force_set in new_forces:
            if len(force_set) != 6:
                raise ValueError("Each force set must be a list of length 6: [Fx, Fy, Fz, Mx, My, Mz].")

        self.latest_forces = new_forces

    def draw_force(self):
        """
        Draw six force/moment components (Fx, Fy, Fz, Mx, My, Mz) in a vertical layout.
        
        Each force component's bars are stacked (one per set),
        and the 'zero' anchor for the bars is placed near the center of the screen,
        so negative values go left, and positive values go right.
        
        The text labels are pinned to the far left, and there's an extra vertical gap
        between different components for clarity.
        """
        font = pygame.font.SysFont("consolas", 16)

        # The six component labels
        labels = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]

        # Layout configuration
        text_x = 20                      # Place text on the far left
        bar_center_x = self.width // 2   # Anchor for zero in the horizontal (center of screen)
        bar_start_y = 50                 # The top Y for the very first component
        set_spacing = 40                 # Vertical distance between sets (Fx1, Fx2, Fx3, etc.)
        extra_gap = 60                   # Extra gap between different components (Fx vs. Fy, etc.)
        bar_height = 16                  # Height of each bar

        # (Optional) draw a vertical reference line at bar_center_x:
        pygame.draw.line(
            self.screen, 
            (180, 180, 180), 
            (bar_center_x, 0), 
            (bar_center_x, self.height), 
            2
        )

        # Loop through each of the 6 components
        for comp_idx, label in enumerate(labels):
            # Calculate the base Y for this component block
            comp_base_y = bar_start_y + comp_idx * (self.num_sets * set_spacing + extra_gap)

            # For each set, draw one bar
            for s_idx in range(self.num_sets):
                # The value for this component in this set
                value = self.latest_forces[s_idx][comp_idx]

                # Compute the Y position for this set's bar in the current component block
                y_pos = comp_base_y + s_idx * set_spacing

                # Create a text label like "Fx1 = 12.345"
                text_str = f"{label}{s_idx+1} = {value:.3f}"
                text_surf = font.render(text_str, True, (255, 255, 255))
                text_w, text_h = text_surf.get_size()
                self.screen.blit(text_surf, (text_x, y_pos))

                # Decide scaling: moments get an extra multiplier
                if label in ["Mx", "My", "Mz"]:
                    scale = self.scale_torque
                else:
                    scale = self.scale_force

                # Calculate bar length in pixels
                length = abs(value) * scale
                if length > self.max_length:
                    length = self.max_length

                # Choose color based on set index
                if s_idx < len(self.set_colors):
                    base_color = self.set_colors[s_idx]
                else:
                    base_color = (255, 255, 255)  # default color if not enough predefined

                # Darken the color if negative
                color_pos = base_color
                color_neg = (
                    max(base_color[0] - 70, 0),
                    max(base_color[1] - 70, 0),
                    max(base_color[2] - 70, 0),
                )

                is_positive = (value >= 0)
                color = color_pos if is_positive else color_neg

                bar_width = int(length)

                # If it's positive, draw to the right of bar_center_x; if negative, to the left
                if is_positive:
                    rect = pygame.Rect(bar_center_x, y_pos, bar_width, bar_height)
                else:
                    rect = pygame.Rect(bar_center_x - bar_width, y_pos, bar_width, bar_height)

                pygame.draw.rect(self.screen, color, rect)

    def draw_legend(self):
        """
        Draw a small legend in the top-right corner, explaining which color
        corresponds to which force set name.
        """
        font = pygame.font.SysFont("consolas", 16)

        # Start from top-right with a little margin
        margin = 10
        legend_x = self.width - 200  # or some other position
        legend_y = margin

        for i, name in enumerate(self.set_names):
            # If we have fewer colors than sets, wrap around or choose default
            if i < len(self.set_colors):
                color = self.set_colors[i]
            else:
                color = (255, 255, 255)

            # Draw a small color box (20x20)
            rect = pygame.Rect(legend_x, legend_y + i*25, 20, 20)
            pygame.draw.rect(self.screen, color, rect)

            # Draw the text
            text_surf = font.render(name, True, (255, 255, 255))
            self.screen.blit(text_surf, (legend_x + 30, legend_y + i*25))

    def stop(self):
        """
        Stop the visualizer thread by setting the running flag to False.
        """
        self.running = False

