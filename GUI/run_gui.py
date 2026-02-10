from PyJEM import TEM3
cl3 = TEM3.Lens3()
try:
    from src.gui.run import main as run
    
    run()
except:
    from src.gui.run import main as run
    
    run()