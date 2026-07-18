import pygame
from PIL import Image, ImageDraw
import os
import json

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720
WORLD_WIDTH = 1700
WORLD_HEIGHT = 1200
PLAYER_SPEED = 4
PLAYER_RADIUS = 16
DEBUG_MODE = True  # Set to True to see collision mask overlay

# Collision boxes (editable with keyboard controls)
COLLISION_BOXES = {
    "1_top_border": {"coords": [(0, 0), (WORLD_WIDTH, 80)], "name": "Top Border"},
    "2_bottom_border": {"coords": [(0, WORLD_HEIGHT - 80), (WORLD_WIDTH, WORLD_HEIGHT)], "name": "Bottom Border"},
    "3_left_border": {"coords": [(0, 0), (80, WORLD_HEIGHT)], "name": "Left Border"},
    "4_right_border": {"coords": [(WORLD_WIDTH - 80, 0), (WORLD_WIDTH, WORLD_HEIGHT)], "name": "Right Border"},
    "5_top_left_building": {"coords": [(250, 150), (550, 400)], "name": "Top-Left Building"},
    "6_top_right_building": {"coords": [(1050, 150), (1450, 400)], "name": "Top-Right Building"},
    "7_farm": {"coords": [(200, 500), (550, 750)], "name": "Farm"},
    "8_large_building": {"coords": [(1050, 450), (1450, 800)], "name": "Large Building"},
    "9_fence": {"coords": [(900, 750), (1400, 950)], "name": "Fence"},
    "0_water": {"coords": [(350, 850), (800, 1100)], "name": "Water"},
}


def load_image(path: str) -> pygame.Surface:
    return pygame.image.load(f"assets/{path}").convert_alpha()


def load_world_background(path: str) -> pygame.Surface:
    image = load_image(path)
    return pygame.transform.scale(image, (WORLD_WIDTH, WORLD_HEIGHT))


def load_collision_mask(path: str) -> pygame.Surface:
    """Load collision mask image for collision detection."""
    return load_image(path)


def generate_collision_mask(path: str) -> None:
    """
    Generate collision mask for Pallet Town using COLLISION_BOXES.
    """
    # Create image with transparent background (walkable areas)
    collision_map = Image.new('RGBA', (WORLD_WIDTH, WORLD_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(collision_map)
    solid_color = (0, 0, 0, 255)  # Black = solid
    
    # Draw all collision boxes
    for box_key, box_data in COLLISION_BOXES.items():
        coords = box_data["coords"]
        draw.rectangle(coords, fill=solid_color)
    
    # Save the collision mask
    collision_map.save(path)
    print(f"✓ Collision mask regenerated: {path}")


def is_walkable(collision_mask: pygame.Surface, x: float, y: float, radius: int) -> bool:
    """Check if a position with radius is walkable on the collision mask."""
    # Sample multiple points around the player's radius for better collision
    sample_points = [
        (int(x), int(y)),                          # Center
        (int(x - radius), int(y)),                 # Left
        (int(x + radius), int(y)),                 # Right
        (int(x), int(y - radius)),                 # Top
        (int(x), int(y + radius)),                 # Bottom
        (int(x - radius), int(y - radius)),        # Top-left
        (int(x + radius), int(y - radius)),        # Top-right
        (int(x - radius), int(y + radius)),        # Bottom-left
        (int(x + radius), int(y + radius)),        # Bottom-right
    ]
    
    for px, py in sample_points:
        # Check bounds
        if px < 0 or px >= WORLD_WIDTH or py < 0 or py >= WORLD_HEIGHT:
            return False
        
        # Get pixel color from collision mask (alpha channel)
        # If alpha > 128, it's solid
        try:
            pixel = collision_mask.get_at((px, py))
            if pixel[3] > 128:  # Alpha channel > 128 means solid
                return False
        except IndexError:
            return False
    
    return True


def update_collision_box(box_key: str, dx: int = 0, dy: int = 0, resize_x: int = 0, resize_y: int = 0) -> None:
    """Update a collision box position or size."""
    if box_key not in COLLISION_BOXES:
        return
    
    coords = COLLISION_BOXES[box_key]["coords"]
    x1, y1 = coords[0]
    x2, y2 = coords[1]
    
    # Move box
    x1 += dx
    y1 += dy
    x2 += dx
    y2 += dy
    
    # Resize box
    x2 += resize_x
    y2 += resize_y
    
    # Keep box within world bounds
    x1 = max(0, min(x1, WORLD_WIDTH - 10))
    y1 = max(0, min(y1, WORLD_HEIGHT - 10))
    x2 = max(x1 + 10, min(x2, WORLD_WIDTH))
    y2 = max(y1 + 10, min(y2, WORLD_HEIGHT))
    
    COLLISION_BOXES[box_key]["coords"] = [(x1, y1), (x2, y2)]


def save_collision_config(filename: str = "maps/collision_config.json") -> None:
    """Save collision box configuration to JSON file."""
    config = {}
    for box_key, box_data in COLLISION_BOXES.items():
        coords = box_data["coords"]
        # Convert to serializable format
        config[box_key] = {
            "name": box_data["name"],
            "coords": [[coords[0][0], coords[0][1]], [coords[1][0], coords[1][1]]]
        }
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Collision config saved to {filename}")


def load_collision_config(filename: str = "maps/collision_config.json") -> None:
    """Load collision box configuration from JSON file."""
    if not os.path.exists(filename):
        return  # File doesn't exist, use defaults
    
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        
        for box_key, box_data in config.items():
            if box_key in COLLISION_BOXES:
                coords = box_data["coords"]
                COLLISION_BOXES[box_key]["coords"] = [
                    (coords[0][0], coords[0][1]),
                    (coords[1][0], coords[1][1])
                ]
        
        print(f"✓ Collision config loaded from {filename}")
    except Exception as e:
        print(f"⚠ Failed to load collision config: {e}")


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Pallet Town Prototype")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # Load collision config from file
    load_collision_config()

    # Generate initial collision mask
    collision_mask_path = "maps/pallet_town_collision.png"
    generate_collision_mask(collision_mask_path)
    collision_mask = load_collision_mask(collision_mask_path)

    background = load_world_background("pallet_town.png")

    world_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
    world_surface.blit(background, (0, 0))

    player_sprites = {
        "stand_left": pygame.transform.scale(load_image("player_stand_left.png"), (96, 96)),
        "stand_right": pygame.transform.scale(load_image("player_stand_right.png"), (96, 96)),
        "stand_up": pygame.transform.scale(load_image("player_stand_back.png"), (96, 96)),
        "stand_down": pygame.transform.scale(load_image("player_stand_front.png"), (96, 96)),
        "walk_left": [
            pygame.transform.scale(load_image("player_left_1.png"), (96, 96)),
            pygame.transform.scale(load_image("player_left_2.png"), (96, 96)),
        ],
        "walk_right": [
            pygame.transform.scale(load_image("player_right_1.png"), (96, 96)),
            pygame.transform.scale(load_image("player_right_2.png"), (96, 96)),
        ],
        "walk_up": [
            pygame.transform.scale(load_image("player_up_1.png"), (96, 96)),
            pygame.transform.scale(load_image("player_up_2.png"), (96, 96)),
        ],
        "walk_down": [
            pygame.transform.scale(load_image("player_down_1.png"), (96, 96)),
            pygame.transform.scale(load_image("player_down_2.png"), (96, 96)),
        ],
    }

    player_pos = pygame.Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
    move_left = False
    move_right = False
    move_up = False
    move_down = False
    running = True
    animation_frame = 0
    direction = "down"
    animation_counter = 0
    
    # Editor variables
    selected_box = "1_top_border"
    box_keys = list(COLLISION_BOXES.keys())
    collision_dirty = False

    pygame.key.set_repeat(500, 100)  # Initial delay: 500ms, repeat: 100ms

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_collision_config()  # Auto-save on exit
                running = False
            elif event.type == pygame.KEYDOWN:
                # Number keys to select collision box (only in debug mode)
                if DEBUG_MODE and event.key == pygame.K_1:
                    selected_box = "1_top_border"
                elif DEBUG_MODE and event.key == pygame.K_2:
                    selected_box = "2_bottom_border"
                elif DEBUG_MODE and event.key == pygame.K_3:
                    selected_box = "3_left_border"
                elif DEBUG_MODE and event.key == pygame.K_4:
                    selected_box = "4_right_border"
                elif DEBUG_MODE and event.key == pygame.K_5:
                    selected_box = "5_top_left_building"
                elif DEBUG_MODE and event.key == pygame.K_6:
                    selected_box = "6_top_right_building"
                elif DEBUG_MODE and event.key == pygame.K_7:
                    selected_box = "7_farm"
                elif DEBUG_MODE and event.key == pygame.K_8:
                    selected_box = "8_large_building"
                elif DEBUG_MODE and event.key == pygame.K_9:
                    selected_box = "9_fence"
                elif DEBUG_MODE and event.key == pygame.K_0:
                    selected_box = "0_water"
                
                # M key to save configuration (only in debug mode)
                elif DEBUG_MODE and event.key == pygame.K_m:
                    save_collision_config()
                
                # Arrow keys to move selected box (only in debug mode)
                elif DEBUG_MODE and event.key == pygame.K_UP:
                    update_collision_box(selected_box, dy=-5)
                    collision_dirty = True
                elif DEBUG_MODE and event.key == pygame.K_DOWN:
                    update_collision_box(selected_box, dy=5)
                    collision_dirty = True
                elif DEBUG_MODE and event.key == pygame.K_LEFT:
                    update_collision_box(selected_box, dx=-5)
                    collision_dirty = True
                elif DEBUG_MODE and event.key == pygame.K_RIGHT:
                    update_collision_box(selected_box, dx=5)
                    collision_dirty = True
                
                # +/- to resize (only in debug mode)
                elif DEBUG_MODE and (event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS):
                    update_collision_box(selected_box, resize_x=5, resize_y=5)
                    collision_dirty = True
                elif DEBUG_MODE and event.key == pygame.K_MINUS:
                    update_collision_box(selected_box, resize_x=-5, resize_y=-5)
                    collision_dirty = True
                
                # Player movement (always active, not just debug)
                elif event.key in (pygame.K_a,):
                    move_left = True
                elif event.key in (pygame.K_d,):
                    move_right = True
                elif event.key in (pygame.K_w,):
                    move_up = True
                elif event.key in (pygame.K_s,):
                    move_down = True
                        
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    move_left = False
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    move_right = False
                elif event.key in (pygame.K_w, pygame.K_UP):
                    move_up = False
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    move_down = False

        # Regenerate collision mask if dirty
        if collision_dirty:
            generate_collision_mask(collision_mask_path)
            collision_mask = load_collision_mask(collision_mask_path)
            collision_dirty = False

        dx = (1 if move_right else 0) - (1 if move_left else 0)
        dy = (1 if move_down else 0) - (1 if move_up else 0)

        if dx != 0 and dy != 0:
            if abs(dx) > abs(dy):
                dy = 0
            else:
                dx = 0
        if dx != 0 or dy != 0:
            movement = pygame.Vector2(dx, dy)
            movement = movement.normalize() * PLAYER_SPEED

            proposed_pos = player_pos + movement
            
            # Check collision with collision mask
            if is_walkable(collision_mask, proposed_pos.x, proposed_pos.y, PLAYER_RADIUS):
                proposed_rect = pygame.Rect(
                    int(proposed_pos.x - PLAYER_RADIUS),
                    int(proposed_pos.y - PLAYER_RADIUS),
                    PLAYER_RADIUS * 2,
                    PLAYER_RADIUS * 2,
                )

                if proposed_rect.left < 0:
                    proposed_pos.x = PLAYER_RADIUS
                elif proposed_rect.right > WORLD_WIDTH:
                    proposed_pos.x = WORLD_WIDTH - PLAYER_RADIUS

                if proposed_rect.top < 0:
                    proposed_pos.y = PLAYER_RADIUS
                elif proposed_rect.bottom > WORLD_HEIGHT:
                    proposed_pos.y = WORLD_HEIGHT - PLAYER_RADIUS

                player_pos = proposed_pos

        if dx < 0:
            direction = "left"
        elif dx > 0:
            direction = "right"
        elif dy < 0:
            direction = "up"
        elif dy > 0:
            direction = "down"

        is_walking = dx != 0 or dy != 0
        if is_walking:
            animation_counter += 1
            if animation_counter >= 10:
                animation_frame = (animation_frame + 1) % 2
                animation_counter = 0
            current_sprite_name = f"walk_{direction}"
            current_sprite = player_sprites[current_sprite_name][animation_frame]
        else:
            animation_counter = 0
            current_sprite_name = f"stand_{direction}"
            current_sprite = player_sprites[current_sprite_name]

        camera_x = max(0, min(WORLD_WIDTH - WINDOW_WIDTH, int(player_pos.x - WINDOW_WIDTH // 2)))
        camera_y = max(0, min(WORLD_HEIGHT - WINDOW_HEIGHT, int(player_pos.y - WINDOW_HEIGHT // 2)))

        screen.fill((0, 0, 0))
        screen.blit(world_surface, (0, 0), (camera_x, camera_y, WINDOW_WIDTH, WINDOW_HEIGHT))

        # Draw collision mask overlay in debug mode
        if DEBUG_MODE:
            collision_overlay = collision_mask.copy()
            collision_overlay.set_alpha(100)  # Semi-transparent
            screen.blit(collision_overlay, (0, 0), (camera_x, camera_y, WINDOW_WIDTH, WINDOW_HEIGHT))

        player_screen_x = int(player_pos.x - camera_x)
        player_screen_y = int(player_pos.y - camera_y)
        sprite_rect = current_sprite.get_rect(center=(player_screen_x, player_screen_y))
        screen.blit(current_sprite, sprite_rect)

        font = pygame.font.SysFont("arial", 24)
        small_font = pygame.font.SysFont("arial", 18)
        
        text = font.render("Pallet Town Prototype", True, (255, 255, 255))
        screen.blit(text, (20, 20))
        
        if DEBUG_MODE:
            # Show collision editor info
            selected_name = COLLISION_BOXES[selected_box]["name"]
            coords = COLLISION_BOXES[selected_box]["coords"]
            x1, y1 = coords[0]
            x2, y2 = coords[1]
            width = x2 - x1
            height = y2 - y1
            
            debug_lines = [
                f"[COLLISION EDITOR]",
                f"Selected: {selected_name} (Press 1-0 to select)",
                f"Position: ({x1}, {y1}) Size: {width}x{height}",
                f"Arrow Keys: Move | +/-: Resize | M: Save",
            ]
            
            for i, line in enumerate(debug_lines):
                debug_text = small_font.render(line, True, (255, 100, 100))
                screen.blit(debug_text, (20, 50 + i * 25))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
