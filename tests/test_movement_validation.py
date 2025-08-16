#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_obvious_movement():
    """Test with commands that should produce obvious movement"""
    
    commands = [
        "(MSG, Testing obvious movement)",
        "G90",  # Absolute positioning
        "G0 Z-100",  # Move to Z-100 (should be obvious movement)
        "G4 P1",  # Pause 1 second
        "G0 Z-120",  # Move to Z-120 (obvious movement back)
    ]
    
    print("Testing with obvious movement commands...")
    print("Watch the machine Z-axis for movement!")
    print()
    
    for i, command in enumerate(commands, 1):
        print(f"=== Command {i}/{len(commands)}: {command} ===")
        
        try:
            # Connect for each command
            print("Connecting...")
            async with websockets.connect("ws://10.1.1.20:8080/websocket") as websocket:
                print("Connected!")
                
                # Wait for initial state
                initial_msg = await websocket.recv()
                data = json.loads(initial_msg)
                if 'zp' in data:
                    print(f"Initial Z position: {data['zp']}")
                
                # Send command
                print(f"Sending: {command}")
                await websocket.send(command + '\n')
                print("✓ Command sent!")
                
                # Wait for response and position update
                print("Waiting for response...")
                timeout_count = 0
                max_timeout = 10
                
                while timeout_count < max_timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)
                        
                        if 'zp' in data:
                            print(f"New Z position: {data['zp']}")
                            break
                        else:
                            print(f"Response: {response[:100]}...")
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        print(f"Waiting... ({timeout_count}/{max_timeout})")
                        
                print("Command completed!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("Waiting before next command...")
        time.sleep(2)
        print()
    
    print("=== Test completed ===")
    print("Did you observe any Z-axis movement on the machine?")

if __name__ == "__main__":
    asyncio.run(test_obvious_movement())